from pymodbus.client import ModbusTcpClient
from time import sleep


class ClienteMODBUS():
    """COMUNICAÇÃO"""
    def __init__(self, server_ip='localhost', porta=502):
        self.server_ip = server_ip
        self.porta = int(porta)
        self._cliente = ModbusTcpClient(host=self.server_ip, port=self.porta)
        self.conectado = False

    def configurar_conexao(self, server_ip, porta):
        """Atualiza IP e porta dinamicamente a partir da interface gráfica."""
        if self.conectado:
            self.desconectar()
        self.server_ip = server_ip
        self.porta = int(porta)
        self._cliente = ModbusTcpClient(host=self.server_ip, port=self.porta)

    def conectar(self):
        try:
            self.conectado = bool(self._cliente.connect())
            return self.conectado
        except Exception:
            self.conectado = False
            return False

    def desconectar(self):
        try:
            self._cliente.close()
        finally:
            self.conectado = False

    def ler_holding_registers(self, addr, count=1):
        try:
            resp = self._cliente.read_holding_registers(address=int(addr), count=int(count), device_id=1)
            if resp and not resp.isError():
                return resp.registers
            return None
        except Exception:
            return None

    def escrever_holding_register(self, addr, valor):
        try:
            resp = self._cliente.write_register(address=int(addr), value=int(valor), device_id=1)
            return bool(resp and not resp.isError())
        except Exception:
            return False

    # 3.0 Leitura e escrita de Coils

    def ler_coils(self, addr, count=1):
        """Lê o estado de uma ou mais bobinas (Coils)."""
        try:
            resp = self._cliente.read_coils(address=int(addr), count=int(count), device_id=1)
            if resp and not resp.isError():
                return resp.bits[:count]
            return None
        except Exception:
            return None

    def escrever_coil(self, addr, valor):
        """Escreve True/False (ou 1/0) em uma bobina (Coil)."""
        try:
            if isinstance(valor, str):
                bool_val = valor.strip().lower() in ('1', 'true', 'on', 'v', 'sim')
            else:
                bool_val = bool(int(valor))
            resp = self._cliente.write_coil(address=int(addr), value=bool_val, device_id=1)
            return bool(resp and not resp.isError())
        except Exception:
            return False

    # 3.1 Leitura e escrita de float

    def ler_float(self, addr):
        """Lê 2 registradores consecutivos e converte para float32."""
        try:
            regs = self.ler_holding_registers(addr, count=2)
            if regs and len(regs) == 2:
                return round(self._cliente.convert_from_registers(regs, self._cliente.DATATYPE.FLOAT32), 4)
            return None
        except Exception:
            return None

    def escreve_float(self, addr, valor_float):
        """Converte float32 para 2 registradores e escreve."""
        try:
            regs = self._cliente.convert_to_registers(float(valor_float), self._cliente.DATATYPE.FLOAT32)
            resp = self._cliente.write_registers(address=int(addr), values=regs, device_id=1)
            return bool(resp and not resp.isError())
        except Exception:
            return False

    # 3.2 Leitura dos bits do registrador (todos, individual ou múltiplos)

    def ler_bits(self, addr, indices_bits=None):
        """
        Lê um registrador e retorna o estado dos bits (0 a 15).
        - Se indices_bits for None ou vazio: retorna lista com os 16 bits.
        - Se indices_bits for passado (ex: '6' ou '0,1,6'): retorna dicionário com os bits pedidos.
        """
        regs = self.ler_holding_registers(addr, count=1)
        if not regs:
            return None
        valor = regs[0]
        todos_bits = [(valor >> i) & 1 for i in range(16)]

        if indices_bits is None or str(indices_bits).strip() == "":
            return todos_bits

        try:
            lista_indices = [int(b.strip()) for b in str(indices_bits).split(',') if b.strip() != ""]
            resultado = {}
            for idx in lista_indices:
                if 0 <= idx <= 15:
                    resultado[f"Bit {idx}"] = todos_bits[idx]
                else:
                    return None
            return resultado
        except Exception:
            return None

    # 3.3 Escrita de um bit individual ou múltiplos bits

    def escreve_bit(self, addr, bit_index, valor_bit):
        """Altera um bit específico para 0 ou 1, preservando os restantes."""
        if not (0 <= int(bit_index) <= 15):
            return False

        regs = self.ler_holding_registers(addr, count=1)
        if regs:
            valor = regs[0]
            if int(valor_bit) == 1:
                valor = valor | (1 << int(bit_index))   # Aplica máscara OR para colocar a 1
            else:
                valor = valor & ~(1 << int(bit_index))  # Aplica máscara AND invertida para colocar a 0

            return self.escrever_holding_register(addr, valor)
        return False

    def escreve_multiplos_bits(self, addr, indices_str, valores_str):
        """
        Altera um ou múltiplos bits de um registrador preservando os restantes.
        - Bit único: indices_str="6", valores_str="1"
        - Múltiplos bits: indices_str="0,1,6", valores_str="1,0,1" (ou "1" para aplicar a todos)
        """
        try:
            regs = self.ler_holding_registers(addr, count=1)
            if not regs:
                return False
            valor_reg = regs[0]

            indices_limpo = str(indices_str).strip()
            valores_limpo = str(valores_str).strip()

            if indices_limpo != "":
                lista_indices = [int(i.strip()) for i in indices_limpo.split(',') if i.strip() != ""]
                lista_valores = [int(v.strip()) for v in valores_limpo.split(',') if v.strip() != ""]

                if len(lista_valores) == 1 and len(lista_indices) > 1:
                    lista_valores = lista_valores * len(lista_indices)

                if len(lista_indices) != len(lista_valores):
                    return False

                for idx, val_bit in zip(lista_indices, lista_valores):
                    if not (0 <= idx <= 15) or val_bit not in (0, 1):
                        return False
                    if val_bit == 1:
                        valor_reg |= (1 << idx)
                    else:
                        valor_reg &= ~(1 << idx)

                return self.escrever_holding_register(addr, valor_reg)

            return False
        except Exception:
            return False