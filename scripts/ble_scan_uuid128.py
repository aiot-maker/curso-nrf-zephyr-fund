import asyncio
import argparse
import struct
from bleak import BleakScanner

mac_filter = None      # Só será preenchido se -m for usado
uuid128_filter = None  # Conjunto de UUIDs canônicos a filtrar (None = filtro inativo)

def load_mac_list(path):
    """Carrega MACs do arquivo (um por linha, maiúsculo)."""
    try:
        with open(path, "r") as f:
            macs = {line.strip().upper() for line in f if line.strip()}
        print(f"✅ Lista de MACs carregada ({len(macs)} entradas).")
        return macs
    except FileNotFoundError:
        print(f"⚠️ Arquivo '{path}' não encontrado – sem filtro de MAC.")
        return None

def load_uuid128_list(path):
    """Carrega UUIDs canônicos do arquivo (um por linha, minúsculo).
    Retorna set() se o arquivo existir mas estiver vazio (filtro ativo, sem permitir nenhum UUID)."""
    try:
        with open(path, "r") as f:
            uuids = {line.strip().lower() for line in f if line.strip()}
        print(f"✅ Lista de UUIDs carregada ({len(uuids)} entradas).")
        return uuids  # pode ser set() (vazio) -> filtro ativo, bloqueando tudo
    except FileNotFoundError:
        print(f"⚠️ Arquivo '{path}' não encontrado – sem filtro de UUID128.")
        return None   # filtro inativo

def get_service_data_payload(advertisement_data):
    """Gera pares (uuid, payload) para cada Service Data presente."""
    sd = advertisement_data.service_data or {}
    for uuid_str, payload in sd.items():
        yield uuid_str.lower(), payload

def parse_service_data(payload):
    """payload[0] -> SENSOR_TYPE; payload[1:3] -> t_centi (s16 LE) se tipo == 1."""
    if not payload or len(payload) < 1:
        return None, None
    sensor_type = payload[0]
    value_bytes = payload[1:3] if len(payload) >= 3 else None
    return sensor_type, value_bytes

def callback(device, advertisement_data):
    """Processa cada advertisement BLE."""
    # Filtro por MAC só se -m foi usado (None = inativo; set() vazio = ainda ativo)
    if mac_filter is not None and device.address.upper() not in mac_filter:
        return

    for uuid_str, payload in get_service_data_payload(advertisement_data):
        # ✅ Filtro de UUID: ativo se uuid128_filter is not None (mesmo se vazio)
        if uuid128_filter is not None and uuid_str not in uuid128_filter:
            continue

        sensor_type, value_bytes = parse_service_data(payload)
        if sensor_type is None:
            continue

        nome = device.name or "Desconhecido"

        if sensor_type == 1 and value_bytes is not None:
            t_centi = struct.unpack("<h", value_bytes)[0]
            temp_c = t_centi / 100.0
            print(f"{device.address}  RSSI {advertisement_data.rssi:>4} dBm  "
                  f"Temp {temp_c:6.2f} °C  UUID: {uuid_str}  Nome: {nome}")
        elif sensor_type != 0:
            print(f"{device.address}  RSSI {advertisement_data.rssi:>4} dBm  "
                  f"Sensor desconhecido (tipo {sensor_type:02X})  UUID: {uuid_str}  Nome: {nome}")
        # tipo == 0 -> silencioso

async def run(scan_time):
    scanner = BleakScanner(callback)
    print("🔎 Iniciando scanner BLE… (Ctrl+C para parar)")
    await scanner.start()
    try:
        if scan_time:
            await asyncio.sleep(scan_time)
        else:
            while True:
                await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n⛔ Interrompido pelo usuário.")
    finally:
        await scanner.stop()
        print("✅ Scanner finalizado.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scanner BLE: filtra Service Data UUID128 e mostra temperatura/sensor"
    )
    parser.add_argument("-m", "--macs", type=str,
                        help="Arquivo com MACs permitidos (um por linha). Se ausente, não filtra.")
    parser.add_argument("-u", "--uuid128", type=str,
                        help="Arquivo com UUIDs 128-bit a filtrar (um por linha, formato canônico).")
    parser.add_argument("-t", "--time", type=int,
                        help="Tempo de varredura em segundos (se omitido, roda continuamente).")
    args = parser.parse_args()

    if args.macs:
        mac_filter = load_mac_list(args.macs)  # None = inativo; set() = ativo
    if args.uuid128:
        uuid128_filter = load_uuid128_list(args.uuid128)  # None = inativo; set() = ativo (bloqueia tudo)

    asyncio.run(run(args.time))
