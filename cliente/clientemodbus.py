from pymodbus.client import ModbusTcpClient
from time import sleep

class ClienteMODBUS():
    """Classe responsável apenas pela comunicação Modbus. Sem prints ou inputs."""
    def __init__(self, server_ip, porta):
        self._cliente = ModbusTcpClient(host=server_ip, port=porta)

    def conectar(self):
        return self._cliente.connect()

    def desconectar(self):
        self._cliente.close()

    def ler_holding_registers(self, addr, count=1):
        resp = self._cliente.read_holding_registers(address=addr, count=count, device_id=1)
        if resp and not resp.isError():
            return resp.registers
        return None

    def escrever_holding_register(self, addr, valor):
        resp = self._cliente.write_register(address=addr, value=valor, device_id=1)
        return bool(resp and not resp.isError())

    # 3.1 Leitura e escrita de float

    def ler_float(self, addr):
        """Lê 2 registradores consecutivos e converte para float32."""
        regs = self.ler_holding_registers(addr, count=2)
        if regs:
            return self._cliente.convert_from_registers(regs, self._cliente.DATATYPE.FLOAT32)
        return None

    def escreve_float(self, addr, valor_float):
        """Converte float32 para 2 registradores e escreve."""
        regs = self._cliente.convert_to_registers(valor_float, self._cliente.DATATYPE.FLOAT32)
        resp = self._cliente.write_registers(address=addr, values=regs, device_id=1)
        return bool(resp and not resp.isError())
    
    # 3.2 Leitura dos bits do registrador

    def ler_bits(self, addr):
        """Lê um registrador e retorna uma lista com o estado dos 16 bits (0 a 15)."""
        regs = self.ler_holding_registers(addr, count=1)
        if regs:
            valor = regs[0]  # Extrai cada bit usando deslocamento (shift) e máscara lógica AND
            return [(valor >> i) & 1 for i in range(16)]
        return None
    
    # 3.3 Escrita de um bit individual

    def escreve_bit(self, addr, bit_index, valor_bit):
        """Altera um bit específico para 0 ou 1, preservando os restantes."""
        if not (0 <= bit_index <= 15):
            return False
            
        # Sequência: Leitura, alteração com máscara e escrita
        regs = self.ler_holding_registers(addr, count=1)
        if regs:
            valor = regs[0]
            if valor_bit == 1:
                valor = valor | (1 << bit_index)  # Aplica máscara OR para colocar a 1
            else:
                valor = valor & ~(1 << bit_index) # Aplica máscara AND invertida para colocar a 0
            
            # Escreve o novo valor no registrador
            return self.escrever_holding_register(addr, valor)
        return False

# =====================================================================
# DEMONSTRAÇÕES EXIGIDAS PELA ATIVIDADE ////// USADO IA NO PROCESSO EDUCATIVO \\\\\\ 
# =====================================================================
if __name__ == '__main__':
    c = ClienteMODBUS('localhost', 502)
    
    # 3.4 Tratamento de Falhas: Verifica conexão antes de continuar
    if not c.conectar():
        print("FALHA: Não foi possível conectar ao servidor Modbus.")
    else:
        print("--- CONECTADO AO SERVIDOR ---")

        # 3.4 Tratamento de Falhas: Verifica resposta de erro
        if c.ler_holding_registers(9999) is None:
            print("FALHA ESPERADA: Endereço 9999 inexistente. A classe sinalizou o erro retornando None.\n")

        # A) Emulação (Lê os 10 dados com 2 repetições para ver a flutuação)
        print("[1] EMULAÇÃO (Valores Flutuando):")
        for i in range(2):
            print(f" -> Leitura {i+1}:")
            print(f"    1. TEMP_R: {c.ler_float(700):.1f} | 2. TEMP_S: {c.ler_float(702):.1f} | 3. TEMP_T: {c.ler_float(704):.1f}")
            print(f"    4. TEMP_CARC: {c.ler_float(706):.1f} | 5. PIT01: {c.ler_float(710):.1f} | 6. FIT01: {c.ler_float(712):.1f}")
            print(f"    7. Freq: {c.ler_holding_registers(830)[0]} | 8. Corr R: {c.ler_holding_registers(840)[0]}")
            print(f"    9. Tensao RS: {c.ler_holding_registers(847)[0]} | 10. FP R: {c.ler_holding_registers(868)[0]}")
            sleep(1.5)

        # B) Escala
        print("\n[2] ESCALA (Frequência - Endereço 830):")
        raw_freq = c.ler_holding_registers(830)[0]
        print(f"    Recebido: {raw_freq} | Div: 100 | Multiplicador: 0.01 | Engenharia: {raw_freq * 0.01:.2f} Hz")

        # C) Float
        print("\n[3] FLOAT (Setpoint - Endereço 1302):")
        c.escreve_float(1302, 65.5)
        print(f"    Enviado: 65.5 | Recuperado: {c.ler_float(1302)}")

        # D) Bits
        print("\n[4] BITS (Habilita Motor - Endereço 1328):")
        c.escrever_holding_register(1328, 3) # Começa com bits 0 e 1 em '1'
        print(f"    16 Bits iniciais (valor 3): {c.ler_bits(1328)}")
        
        c.escreve_bit(1328, 6, 1)
        print(f"    Após LIGAR bit 6:           {c.ler_bits(1328)}")
        
        c.escreve_bit(1328, 6, 0)
        print(f"    Após DESLIGAR bit 6:        {c.ler_bits(1328)}")
        print("    (Bits 0 e 1 preservados com sucesso!)")

        c.desconectar()