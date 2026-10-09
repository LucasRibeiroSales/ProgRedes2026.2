# Telemetria BitDogLab

Projeto didático que envia leituras em milímetros do VL53L0X por TCP e grava os dados em SQLite no computador. O servidor mostra a média das leituras dos últimos 5 minutos e da última hora.

## Arquivos

- `main.py`: cliente MicroPython da BitDogLab.
- `servidor.py`: servidor TCP e criação automática de `telemetria.db` e da tabela `leituras`.
- `vl53l0x.py`: driver MicroPython do sensor, copiado para a placa.

## Ligações e configuração da placa

Ligue VCC e GND do VL53L0X à alimentação compatível e SDA/SCL ao barramento I2C0. A pinagem informada pela documentação da BitDogLab é **GP0 = SDA** e **GP1 = SCL**, igual à configuração de `main.py`. Confirme também a tensão compatível com o módulo do sensor. Configure o SSID, a senha e o IP do computador no início de `main.py`. O IP da placa deve ser o endereço do computador acessível pela rede Wi-Fi; `0.0.0.0` é apenas o endereço em que o servidor aceita conexões.

O cliente usa o driver MicroPython [MicroPython_VL53L0X](https://github.com/kapetan/MicroPython_VL53L0X). Copie o arquivo `vl53l0x.py` desse repositório para a placa junto com `main.py`. A API usada é `VL53L0X(i2c)` e a leitura em milímetros é `sensor.range`.

## Execução

1. No computador, execute `python servidor.py` (Windows: `py servidor.py`). O servidor escuta na porta TCP 6666 e cria o banco automaticamente.
2. Edite as configurações de rede e hardware em `main.py` e transfira-o, junto com o driver, para a BitDogLab.
3. Reinicie/execute `main.py` na placa. O terminal do computador deve mostrar dispositivo, distância e as duas médias. Os dados ficam no arquivo `telemetria.db` na pasta de execução do servidor.

Quando ainda não houver leituras no período, o terminal informa “sem leituras no período”. A coluna `instante` usa o horário UTC gerado pelo SQLite (`CURRENT_TIMESTAMP`); as consultas usam `datetime('now', ...)`, também em UTC.

## Verificações antes da entrega

- Confirmar fisicamente SDA/SCL, I2C0, alimentação e endereço/resposta do sensor.
- Preencher credenciais Wi-Fi e o IPv4 do computador; permitir a porta 6666 no firewall/rede local.
- Enviar várias leituras, verificar as linhas na tabela `leituras` e acompanhar as médias.
- Desconectar/reconectar a placa e enviar uma linha malformada de um cliente TCP para verificar a continuidade do servidor.
- Executar testes em computador não substitui a validação com a BitDogLab e o sensor reais.
