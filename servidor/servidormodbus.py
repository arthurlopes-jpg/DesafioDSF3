from pyModbusTCP.server import ModbusServer, DataBank
import random
import struct
from time import sleep

class ServidorMODBUS():
    def __init__(self, host_ip, port):
        # Cria o banco de dados e o servidor (formato moderno)
        self._db = DataBank()
        self._server = ModbusServer(host=host_ip, port=port, no_block=True, data_bank=self._db)
        
        # Inicialização do Mapa de Dados
        self.set_float(700, 25.0 * 10)  
        self.set_float(702, 25.5 * 10)  
        self.set_float(704, 24.8 * 10)  
        self.set_float(706, 35.0 * 10)  
        self.set_float(710, 1.2 * 1)    
        self.set_float(712, 0.0 * 1)    # fit01 - Vazão 
        self.set_float(1302, 50.0 * 1)  # sp_pid - Setpoint Vazão
        
        self._db.set_holding_registers(830, [6000]) 
        self._db.set_holding_registers(840, [123])  
        self._db.set_holding_registers(847, [3800]) 
        self._db.set_holding_registers(868, [950])  
        self._db.set_holding_registers(1328, [0])   # habilita 

    def set_float(self, address, value):
        packed = struct.pack('>f', value)
        regs = struct.unpack('>HH', packed)
        self._db.set_holding_registers(address, list(regs))

    def get_float(self, address):
        regs = self._db.get_holding_registers(address, 2)
        if regs and len(regs) == 2:
            packed = struct.pack('>HH', regs[0], regs[1])
            return struct.unpack('>f', packed)[0]
        return 0.0

    def run(self):
        try:
            self._server.start()
            print("Servidor MODBUS (Emulador CLP) em execução")
            while True:
                regs_habilita = self._db.get_holding_registers(1328)
                habilita_bit6 = (regs_habilita[0] >> 6) & 1 if regs_habilita else 0
                
                sp_pid = self.get_float(1302)
                fit01 = self.get_float(712)
                
                # Lógica simples: aproxima do setpoint se habilitada; permanece constante se desabilitada
                if habilita_bit6 == 1:
                    if fit01 < sp_pid: 
                        fit01 += 2.5
                    elif fit01 > sp_pid: 
                        fit01 -= 2.5
                
                if fit01 < 0: 
                    fit01 = 0.0
                    
                self.set_float(712, fit01)

                # Leitura (valor de engenharia = valor armazenado / D)
                temp_r_engenharia = self.get_float(700) / 10.0
                
                # Flutuação temporal no valor de engenharia
                temp_r_engenharia += random.uniform(-0.5, 0.5)
                
                # Escrita (valor armazenado = valor de engenharia * D)
                self.set_float(700, temp_r_engenharia * 10.0)
                
                print('===================================')
                print(f"Habilita (Bit 6): {habilita_bit6} | SP_PID: {sp_pid:.1f}")
                print(f"FIT01 (Vazão atual): {fit01:.1f} | TEMP_R (Engenharia): {temp_r_engenharia:.2f}")
                sleep(1)
                
        except Exception as e:
            print("Erro: ", e.args)