import asyncio
import argparse
import struct
from bleak import BleakScanner

mac_filter = None  # Só será preenchido se -m for usado

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

def parse_sensor_type_and_value(advertisement_data):
    """
    Extrai tipo de sensor e valor do Manufacturer Data (Company ID 0xFFFF).
    Byte 0: tipo do sensor
    Bytes 1-2: valor (temperatura em centi-°C se tipo == 1)
    """
    payload = advertisement_data.manufacturer_data.get(0xFFFF)
    if not payload or len(payload) < 3:
        return None, None
    sensor_type = payload[0]
    value_bytes = payload[1:3]
    return sensor_type, value_bytes

def callback(device, advertisement_data):
    """Processa cada advertisement BLE."""
    if mac_filter and device.address.upper() not in mac_filter:
        return

    sensor_type, value_bytes = parse_sensor_type_and_value(advertisement_data)
    if sensor_type is None:
        return

    nome = device.name or "Desconhecido"

    if sensor_type == 1:
        # Temperatura: interpreta os 2 bytes como s16 little-endian
        t_centi = struct.unpack("<h", value_bytes)[0]
        temp_c = t_centi / 100.0
        print(f"{device.address}  RSSI {advertisement_data.rssi:>4} dBm  "
              f"Temp {temp_c:6.2f} °C  Nome: {nome}")
    elif sensor_type != 0:
        print(f"{device.address}  RSSI {advertisement_data.rssi:>4} dBm  "
              f"Sensor desconhecido (tipo {sensor_type:02X})  Nome: {nome}")
    # Se sensor_type == 0, ignora o pacote (pode ser reservado ou inválido)

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
        description="Scanner BLE: identifica tipo de sensor no Manufacturer Data (Company ID 0xFFFF)"
    )
    parser.add_argument("-m", "--macs", type=str,
                        help="Arquivo com MACs permitidos (um por linha). Se ausente, não filtra.")
    parser.add_argument("-t", "--time", type=int,
                        help="Tempo de varredura em segundos (se omitido, roda continuamente).")
    args = parser.parse_args()

    if args.macs:
        mac_filter = load_mac_list(args.macs)

    asyncio.run(run(args.time))
