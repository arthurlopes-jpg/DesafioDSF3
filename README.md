# DesafioDSF3


# Aplicação Gráfica Cliente/Servidor Modbus TCP com KivyMD

Aplicação gráfica desenvolvida em Python utilizando **KivyMD** para leitura e escrita de dados em um servidor **Modbus TCP**, mantendo separação estrita de responsabilidades entre a camada de comunicação (`ClienteMODBUS`) e a interface gráfica (`ModbusApp`).

---

## Funcionalidades Implementadas

- Campos para digitar IP e Porta do servidor com botão de Conectar / Desconectar
- Operações de Leitura e Escrita (Menu `MDDropdownMenu`)
  - **Holding Registers:** Leitura e escrita de registradores inteiros de 16 bits.
  - **Coils:** Leitura e escrita de bobinas (`True`/`False` ou `1`/`0`).
  - **Valores Float:** Leitura e escrita de valores em ponto flutuante IEEE 754 (`FLOAT32` ocupando 2 registradores consecutivos).
  - **Bits de Registrador:** Leitura dos 16 bits, de um bit individual ou de múltiplos bits específicos, e escrita de bit único ou múltiplos bits preservando os demais via máscara bitwise.
- **Leitura Recorrente Automática:** Opção selecionável via `MDCheckbox` que realiza leituras periódicas a cada 1 segundo utilizando o módulo `Clock` do Kivy (`Clock.schedule_interval`).

---
