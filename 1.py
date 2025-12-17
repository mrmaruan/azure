import requests, json, time, random, winsound
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo  # py3.9+
except ImportError:
    from backports.zoneinfo import ZoneInfo  # si tu Python es más viejo

URL_BASE   = "https://citaprevia.ciencia.gob.es/qmaticwebbooking/rest"
UI_BASE    = "https://citaprevia.ciencia.gob.es/qmaticwebbooking/"
BRANCH_ID  = "7c2c5344f7ec051bc265995282e38698f770efab83ed9de0f9378d102f700630"
SERVICE_ID = "e97539664874283b583f0ff0b25d1e34f0f14e083d59fb10b2dafb76e4544019"

DATE        = "2025-12-15"
TIME        = "12:00"
CUSTOM_SLOT = 10
QUERY_SLOT  = 1

CUSTOMER = {
    "firstName": "Nombre",
    "lastName":  "Apellidos",
    "custRef":   "Pasaporte-DNI-NIE",
    "phone":     "Telefono",
    "email":     "Correo",
}

RELEASE_DAYS = {6, 0, 1, 2}
WINDOW_START = (12, 00)
WINDOW_END   = (14, 50)
STEP_MIN     = 0.001
CHASE_AFTER_S = 1.0
POLL_MS       = 5
MAX_RETRIES   = 4
RETRY_DELAY   = 0.01

AUTO_RESTART_DELAY = 0.0001
MAX_RESTART_ATTEMPTS = 100000

MAX_OFFSET_SECONDS = 2.5
MIN_OFFSET_SECONDS = -2.5

# ⭐ NUEVO: Configuración específica para ERROR_SESSIÓN_VIOLATION
SESSION_VIOLATION_RETRY_DELAY = 0.001  # delay antes de reintentar tras violación de sesión
MAX_SESSION_VIOLATION_RETRIES = 50     # número de reintentos antes de reinicio completo

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://citaprevia.ciencia.gob.es",
    "Referer": UI_BASE,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.8",
    "Content-Type": "application/json",
    "X-Requested-With": "XMLHttpRequest",
})

# ⭐ NUEVO: Excepción personalizada
class SessionViolationError(Exception):
    """Excepción lanzada cuando se detecta ERROR_SESSIÓN_VIOLATION"""
    pass

def reset_session():
    """Limpia la sesión actual y crea una nueva"""
    global session
    session.close()
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://citaprevia.ciencia.gob.es",
        "Referer": UI_BASE,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "es-ES,es;q=0.8",
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
    })

# ⭐ MODIFICADO: Detección de ERROR_SESSIÓN_VIOLATION
def check_session_violation(response):
    """Verifica si la respuesta contiene ERROR_SESSIÓN_VIOLATION"""
    try:
        # Verificar en el JSON
        if response.headers.get('content-type', '').startswith('application/json'):
            data = response.json()
            if isinstance(data, dict):
                error_code = data.get('errorCode', '')
                error_msg = data.get('error', '')
                message = data.get('message', '')
                
                if ('SESSION_VIOLATION' in str(error_code) or 
                    'SESSION_VIOLATION' in str(error_msg) or
                    'SESSION_VIOLATION' in str(message)):
                    return True
        
        # Verificar en el texto de la respuesta
        if 'SESSION_VIOLATION' in response.text or 'SESSION_VIOLATION' in response.text:
            return True
            
    except Exception:
        pass
    
    return False

# ⭐ MODIFICADO: request con manejo de violación de sesión
def req(method, url, **kwargs):
    """Ejecuta request con auto-refresh de CSRF y detección de violación de sesión"""
    try:
        r = session.request(method, url, **kwargs)
    except Exception as e:
        time.sleep(0.15)
        r = session.request(method, url, **kwargs)
    
    # ⭐ NUEVO: Verificar violación de sesión
    if check_session_violation(r):
        print("🚨 ERROR_SESSION_VIOLATION detectado en la respuesta")
        raise SessionViolationError("Violación de sesión detectada")
    
    new_csrf = r.headers.get("x-csrf-token")
    if new_csrf:
        session.headers["x-csrf-token"] = new_csrf
    return r

def _cookie_in_session():
    return session.cookies.get("JSESSIONID") or None

def _cookie_from_headers(headers: dict):
    sc = headers.get("Set-Cookie") or headers.get("set-cookie")
    if sc and "JSESSIONID=" in sc:
        return sc.split("JSESSIONID=")[1].split(";")[0].strip()
    return None

def _ensure_cookie_header(js):
    session.headers["Cookie"] = f"JSESSIONID={js}"

def iniciar_sesion():
    """Inicializa sesión con manejo de violaciones"""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            # CSRF
            cfg = req("GET", f"{URL_BASE}/schedule/configuration", allow_redirects=False)
            cfg.raise_for_status()
            csrf = cfg.json().get("token")
            if not csrf:
                raise RuntimeError("No pude obtener CSRF desde /schedule/configuration")
            session.headers["x-csrf-token"] = csrf
            print("🔑 CSRF:", csrf[:40], "...")

            # JSESSIONID
            r_ui = req("GET", UI_BASE, allow_redirects=True)
            r_ui.raise_for_status()
            js = _cookie_in_session()
            if not js:
                for hop in ([r_ui] + list(getattr(r_ui, "history", []))):
                    js = _cookie_from_headers(hop.headers)
                    if js:
                        session.cookies.set("JSESSIONID", js,
                            domain="citaprevia.ciencia.gob.es",
                            path="/qmaticwebbooking")
                        break
            if js:
                _ensure_cookie_header(js)
                print("🍪 JSESSIONID (UI):", js)
                return

            for url in [f"{URL_BASE}/schedule/branches",
                        f"{URL_BASE}/schedule/branches/{BRANCH_ID}/services"]:
                r = req("GET", url, allow_redirects=False)
                js = _cookie_from_headers(r.headers) or _cookie_in_session()
                if js:
                    session.cookies.set("JSESSIONID", js,
                        domain="citaprevia.ciencia.gob.es",
                        path="/qmaticwebbooking")
                    _ensure_cookie_header(js)
                    print(f"🍪 JSESSIONID (REST init): {js}")
                    return
            raise RuntimeError("No se pudo obtener JSESSIONID (sin Set-Cookie).")
            
        except SessionViolationError:
            if attempt < max_attempts - 1:
                print(f"🔄 Violación de sesión en inicio - reintentando ({attempt+1}/{max_attempts})...")
                reset_session()
                time.sleep(SESSION_VIOLATION_RETRY_DELAY)
            else:
                raise

def server_now_utc():
    r = req("HEAD", f"{URL_BASE}/schedule/configuration")
    if r.status_code >= 400 or "Date" not in r.headers:
        r = req("GET", f"{URL_BASE}/schedule/configuration", allow_redirects=False)
    r.raise_for_status()
    return parsedate_to_datetime(r.headers["Date"])

def server_now(tz: ZoneInfo):
    return server_now_utc().astimezone(tz)

def measure_drift_ms(samples=5):
    from datetime import timezone
    drifts = []
    for _ in range(samples):
        t0 = datetime.now(timezone.utc)
        try:
            srv = server_now_utc()
        except Exception as e:
            print("⚠️ Error midiendo server_now_utc:", e)
            time.sleep(0.1)
            continue
        t1 = datetime.now(timezone.utc)
        midpoint = t0 + (t1 - t0)/2
        drifts.append((srv - midpoint).total_seconds() * 1000.0)
        time.sleep(0.12)
    if not drifts:
        return 0.0
    return sum(drifts) / len(drifts)

def get_service_meta():
    r = req("GET", f"{URL_BASE}/schedule/branches/{BRANCH_ID}/services")
    r.raise_for_status()
    items = r.json() if isinstance(r.json(), list) else []
    name, qp = "Servicio", "3"
    for s in items:
        if str(s.get("publicId")) == str(SERVICE_ID):
            name = s.get("name") or name
            qpv = s.get("qpId")
            qp = str(qpv) if qpv is not None else qp
            break
    return name, qp

# ⭐ MODIFICADO: con manejo de violación de sesión
def list_times_nocache(date_str, service_id, slot_len=1):
    """Lista tiempos con reintento automático en caso de violación de sesión"""
    for attempt in range(MAX_SESSION_VIOLATION_RETRIES):
        try:
            ts = int(time.time()*1000) + random.randint(0,999)
            url = (f"{URL_BASE}/schedule/branches/{BRANCH_ID}/dates/{date_str}/times"
                   f";servicePublicId={service_id};customSlotLength={slot_len}")
            headers = dict(session.headers)
            headers.update({
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "If-Modified-Since": "Mon, 26 Jul 1997 05:00:00 GMT"
            })
            r = req("GET", url, headers=headers)
            r.raise_for_status()
            arr = r.json() if isinstance(r.json(), list) else []
            return [x.get("time") for x in arr]
            
        except SessionViolationError:
            if attempt < MAX_SESSION_VIOLATION_RETRIES - 1:
                print(f"🔄 Violación de sesión en list_times - reintentando ({attempt+1}/{MAX_SESSION_VIOLATION_RETRIES})...")
                time.sleep(SESSION_VIOLATION_RETRY_DELAY)
                reset_session()
                iniciar_sesion()
            else:
                raise

def live_countdown_to(target_dt: datetime, tz: ZoneInfo, label: str):
    print(f"⏳ Esperando al bloque {label} ({target_dt.strftime('%Y-%m-%d %H:%M:%S')}) → "
          f"consultando /times de {DATE} …")
    while True:
        now = server_now(tz)
        remaining = (target_dt - now).total_seconds()
        if remaining <= 0:
            print("\r⏱️ 00:00.0 ")
            break
        if remaining > 3600:
            d  = int(remaining // 86400)
            h  = int((remaining % 86400) // 3600)
            m  = int((remaining % 3600) // 60)
            s  = int(remaining % 60)
            print(f"\r⏱️ T- {d}d {h:02}:{m:02}:{s:02}", end="", flush=True)
            time.sleep(1)
        else:
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            dec  = int((remaining - int(remaining)) * 10)
            print(f"\r⏱️ {mins:02d}:{secs:02d}.{dec}", end="", flush=True)
            time.sleep(0.1)

def iterate_upcoming_boundaries(days_ahead=7):
    tz = ZoneInfo("Europe/Madrid")
    base = server_now(tz)

    def day_bounds(day_dt):
        start = day_dt.replace(hour=WINDOW_START[0], minute=WINDOW_START[1], second=0, microsecond=0)
        end   = day_dt.replace(hour=WINDOW_END[0],   minute=WINDOW_END[1],   second=0, microsecond=0)
        cur = start
        while cur <= end:
            yield cur
            cur = cur + timedelta(minutes=STEP_MIN)

    for add in range(0, days_ahead+1):
        d = (base + timedelta(days=add)).date()
        dt0 = datetime(d.year, d.month, d.day, tzinfo=tz)
        if dt0.weekday() not in RELEASE_DAYS:
            continue
        for b in day_bounds(dt0):
            if b > base:
                yield b

def announce_api_state(target_date: str, prefer_time: str or None):
    try:
        times = list_times_nocache(target_date, SERVICE_ID, QUERY_SLOT)
    except Exception as e:
        print(f"⚠️ No se pudo leer /times de {target_date}: {e}")
        return
    if not times:
        print(f"🔎 API /times {target_date}: ∅ sin citas visibles todavía.")
        return
    prefer_ok = (prefer_time in times) if prefer_time else False
    pref_txt = f" | preferida {prefer_time}: {'✅' if prefer_ok else '❌'}" if prefer_time else ""
    muestra = ", ".join(times[:8]) + ("…" if len(times) > 8 else "")
    print(f"🔎 API /times {target_date}: {len(times)} slots{pref_txt}")
    print(f"   Ejemplo: {muestra}")

# ⭐ MODIFICADO: con manejo de violación de sesión
def reservar_slot_at(time_str, service_name, qp_id):
    """Reserva slot con manejo de violación de sesión"""
    for attempt in range(MAX_SESSION_VIOLATION_RETRIES):
        try:
            url = f"{URL_BASE}/schedule/branches/{BRANCH_ID}/dates/{DATE}/times/{time_str}/reserve;customSlotLength={CUSTOM_SLOT}"
            reserve_custom = json.dumps({
                "peopleServices": [{
                    "publicId": SERVICE_ID,
                    "qpId": str(qp_id),
                    "adult": 1,
                    "name": service_name,
                    "child": 0
                }]
            })
            payload = {"services": [{"publicId": SERVICE_ID}], "custom": reserve_custom}
            r = req("POST", url, data=json.dumps(payload))
            print(f"📟 reserve[{time_str}] →", r.status_code, r.text[:200])
            if r.status_code != 200:
                return None, None
            data = r.json()
            pid = data.get("publicId")
            if not pid:
                return None, None
            return pid, {"service_name": service_name, "qp_id": str(qp_id), "chosen_time": time_str}
            
        except SessionViolationError:
            if attempt < MAX_SESSION_VIOLATION_RETRIES - 1:
                print(f"🔄 Violación de sesión en reserve - reintentando ({attempt+1}/{MAX_SESSION_VIOLATION_RETRIES})...")
                time.sleep(SESSION_VIOLATION_RETRY_DELAY)
                reset_session()
                iniciar_sesion()
            else:
                raise

def check_multiple(chosen_time: str):
    url = (
        f"{URL_BASE}/schedule/appointments/checkMultiple;"
        f"phone={CUSTOMER['phone']};email={CUSTOMER['email']};custRef={CUSTOMER['custRef']};"
        f"firstName={CUSTOMER['firstName']};lastName={CUSTOMER['lastName']};"
        f"branchPublicId={BRANCH_ID};servicePublicId={SERVICE_ID};date={DATE};time={chosen_time}"
    )
    r = req("GET", url)
    print("📟 checkMultiple →", r.status_code, r.text[:200])
    r.raise_for_status()
    return r.json()

def match_customer():
    url = f"{URL_BASE}/schedule/matchCustomer"
    payload = {
        "email": CUSTOMER["email"],
        "phone": CUSTOMER["phone"],
        "firstName": CUSTOMER["firstName"],
        "lastName": CUSTOMER["lastName"],
        "dateOfBirth": "",
        "externalId": CUSTOMER["custRef"],
    }
    r = req("POST", url, data=json.dumps(payload))
    print("📟 matchCustomer →", r.status_code, r.text[:400])
    r.raise_for_status()
    return r.json()

# ⭐ MODIFICADO: con manejo de violación de sesión
def confirmar(publicId, meta):
    """Confirma cita con manejo de violación de sesión"""
    for attempt in range(MAX_SESSION_VIOLATION_RETRIES):
        try:
            service_name = meta["service_name"]
            qp_id       = meta["qp_id"]
            url = f"{URL_BASE}/schedule/appointments/{publicId}/confirm"
            confirm_custom = json.dumps({
                "peopleServices": [{
                    "publicId": SERVICE_ID,
                    "qpId": str(qp_id),
                    "adult": 1,
                    "name": service_name,
                    "child": 0
                }],
                "totalCost": 0,
                "createdByUser": "Qmatic Web Booking",
                "paymentRef": "",
                "customSlotLength": CUSTOM_SLOT
            })
            confirm_payload = {
                "customer": {
                    "firstName": CUSTOMER["firstName"],
                    "lastName":  CUSTOMER["lastName"],
                    "dateOfBirth": "",
                    "email":  CUSTOMER["email"],
                    "phone":  CUSTOMER["phone"],
                    "dob": "",
                    "externalId": CUSTOMER["custRef"],
                },
                "languageCode": "es",
                "countryCode": "es",
                "notificationType": "",
                "captcha": "",
                "custom": confirm_custom,
                "notes": "",
                "title": "Qmatic Web Booking"
            }
            print("🔐 CSRF antes de confirm:", session.headers.get("x-csrf-token", "")[:40], "...")
            r = req("POST", url, json=confirm_payload)
            print("📟 confirm →", r.status_code)
            if r.status_code >= 500:
                print("🧯 HTML error (truncado):\n", r.text[:1500])
            r.raise_for_status()
            data = r.json()
            print("🎉 status:", data.get("status"), " | externalId:", data.get("externalId"))
            return data.get("externalId")
            
        except SessionViolationError:
            if attempt < MAX_SESSION_VIOLATION_RETRIES - 1:
                print(f"🔄 Violación de sesión en confirm - reintentando ({attempt+1}/{MAX_SESSION_VIOLATION_RETRIES})...")
                time.sleep(SESSION_VIOLATION_RETRY_DELAY)
                reset_session()
                iniciar_sesion()
            else:
                raise

def snipe_release_window(prefer_time: str or None = None, stop_after_success=True, days_scan=7):
    svc_name, qp_id = get_service_meta()
    tz = ZoneInfo("Europe/Madrid")

    upcoming = list(iterate_upcoming_boundaries(days_ahead=days_scan))
    if not upcoming:
        print("∅ No hay bloques de liberación en la ventana de días configurada.")
        return None

    vista = ", ".join(b.strftime("%d-%m %H:%M") for b in upcoming[:6])
    print(f"📅 Próximos bloques: {vista}  (la consulta será para {DATE})")

    for target in upcoming:
        drift_ms = measure_drift_ms(samples=5)
        offset_seconds = -drift_ms / 1000.0

        if offset_seconds > MAX_OFFSET_SECONDS:
            offset_seconds = MAX_OFFSET_SECONDS
        elif offset_seconds < MIN_OFFSET_SECONDS:
            offset_seconds = MIN_OFFSET_SECONDS

        print(f"🔍 drift: {drift_ms:+.1f} ms → offset aplicado: {offset_seconds:+.3f} s")

        start_shot = target + timedelta(seconds=offset_seconds)

        now = server_now(tz)
        if now < start_shot:
            announce_api_state(DATE, prefer_time)
            live_countdown_to(start_shot, tz, label="de liberación")

        _ = req("HEAD", f"{URL_BASE}/schedule/configuration")

        deltas = [-1.00, -0.50, -0.35, -0.20, -0.15, -0.10, -0.05, 0.00, 0.03, 0.05, 0.10, 0.15, 0.18, 0.19, 0.20, 0.50, 1.00]
        for d in deltas:
            while True:
                now = server_now(tz)
                if (now - start_shot).total_seconds() >= d:
                    break
                time.sleep(0.005)

            try:
                times = list_times_nocache(DATE, SERVICE_ID, QUERY_SLOT)
            except Exception as e:
                print("⚠️ /times error:", e)
                continue

            if not times:
                print(f"∅ Sin slots en ráfaga {d:+.2f}s")
                continue

            cand = prefer_time if (prefer_time and prefer_time in times) else times[0]
            ejemplo = ", ".join(times[:6]) + ("…" if len(times) > 6 else "")
            print(f"🎯 Ráfaga {d:+.2f}s — {len(times)} slots. Elegido: {cand} | ej: {ejemplo}")

            for attempt in range(MAX_RETRIES):
                pid, meta = reservar_slot_at(cand, svc_name, qp_id)
                if pid:
                    try:
                        check_multiple(cand)
                        match_customer()
                        numero = confirmar(pid, meta)
                        print(f"✅ ¡Cita confirmada {cand}! Nº: {numero}")
                        if stop_after_success:
                            return numero
                    except Exception as e:
                        print(f"🧯 confirm falló (intento {attempt+1}/{MAX_RETRIES}):", e)
                else:
                    print(f"🔁 retry {attempt+1}/{MAX_RETRIES} — aún no se puede reservar {cand}")
                time.sleep(RETRY_DELAY)

        deadline = target + timedelta(seconds=CHASE_AFTER_S)
        while server_now(tz) < deadline:
            try:
                times = list_times_nocache(DATE, SERVICE_ID, QUERY_SLOT)
            except Exception:
                time.sleep(POLL_MS/1000.0)
                continue

            if times:
                cand = prefer_time if (prefer_time and prefer_time in times) else times[0]
                lag = (server_now(tz) - target).total_seconds()
                print(f"🚨 Chase +{lag:.2f}s — captado {len(times)} slots. Voy a por {cand}")
                for attempt in range(MAX_RETRIES):
                    pid, meta = reservar_slot_at(cand, svc_name, qp_id)
                    if pid:
                        try:
                            check_multiple(cand)
                            match_customer()
                            numero = confirmar(pid, meta)
                            print(f"✅ ¡Cita confirmada {cand}! Nº: {numero}")
                            if stop_after_success:
                                return numero
                        except Exception as e:
                            print(f"🧯 confirm falló (chase intento {attempt+1}/{MAX_RETRIES}):", e)
                    else:
                        print(f"🔁 retry {attempt+1}/{MAX_RETRIES} — aún no se puede reservar {cand}")
                    time.sleep(RETRY_DELAY)
            time.sleep(POLL_MS/1000.0)

        print("⏭️ Siguiente bloque…")

    print("🏁 Fin de bloques en el rango de días configurado.")
    return None

# ⭐ MODIFICADO: Main con manejo específico de SessionViolationError
def main():
    restart_count = 0
    
    while restart_count < MAX_RESTART_ATTEMPTS:
        try:
            print(f"\n{'='*60}")
            if restart_count > 0:
                print(f"🔄 REINICIO #{restart_count}")
            print(f"{'='*60}\n")
            
            reset_session()
            iniciar_sesion()
            result = snipe_release_window(prefer_time=TIME, stop_after_success=True, days_scan=7)
            
            if result:
                print(f"\n🎊 ¡ÉXITO! Cita obtenida. Número: {result}")
                winsound.Beep(1000, 500)
                break
            else:
                print("\n⚠️ No se pudo obtener cita en este ciclo.")
                restart_count += 1
        
        # ⭐ NUEVO: Manejo específico de violación de sesión
        except SessionViolationError:
            restart_count += 1
            print(f"\n🔴 ERROR_SESSIÓN_VIOLATION detectado después de múltiples reintentos")
            print(f"🔄 Reiniciando sesión completa... (intento {restart_count}/{MAX_RESTART_ATTEMPTS})")
            time.sleep(AUTO_RESTART_DELAY)
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [400, 504]:
                restart_count += 1
                print(f"\n🔴 ERROR {e.response.status_code} detectado")
                print(f"🔄 Reiniciando en {AUTO_RESTART_DELAY} segundos... (intento {restart_count}/{MAX_RESTART_ATTEMPTS})")
                time.sleep(AUTO_RESTART_DELAY)
            else:
                print(f"\n🔴 Error HTTP no recuperable: {e}")
                raise
                
        except requests.exceptions.ConnectionError as e:
            restart_count += 1
            print(f"\n🔴 ERROR DE CONEXIÓN: {str(e)[:200]}")
            print(f"🔄 Reiniciando en {AUTO_RESTART_DELAY} segundos... (intento {restart_count}/{MAX_RESTART_ATTEMPTS})")
            time.sleep(AUTO_RESTART_DELAY)
            
        except KeyboardInterrupt:
            print("\n🛑 Cancelado por el usuario. Saliendo limpio.")
            break
            
        except Exception as e:
            restart_count += 1
            print(f"\n🔴 ERROR INESPERADO: {type(e).__name__}: {e}")
            print(f"🔄 Reiniciando en {AUTO_RESTART_DELAY} segundos... (intento {restart_count}/{MAX_RESTART_ATTEMPTS})")
            time.sleep(AUTO_RESTART_DELAY)
    
    if restart_count >= MAX_RESTART_ATTEMPTS:
        print(f"\n❌ Se alcanzó el límite máximo de reinicios ({MAX_RESTART_ATTEMPTS}). Abortando.")

if __name__ == "__main__":
    main()
