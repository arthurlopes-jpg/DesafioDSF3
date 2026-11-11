import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from clientemodbus import ClienteMODBUS

Window.size = (500, 660)

KV = '''
MDBoxLayout:
    orientation: 'vertical'
    padding: dp(20)
    spacing: dp(12)

    MDLabel:
        text: "Cliente Modbus TCP - KivyMD"
        halign: "center"
        font_style: "H6"
        size_hint_y: None
        height: dp(35)

    # --- Seção de Conexão (IP, Porta e Botão Conectar) ---
    MDBoxLayout:
        orientation: 'horizontal'
        spacing: dp(10)
        size_hint_y: None
        height: dp(60)

        MDTextField:
            id: ip_field
            text: "localhost"
            hint_text: "IP do Servidor"
            size_hint_x: 0.45

        MDTextField:
            id: port_field
            text: "502"
            hint_text: "Porta"
            input_filter: "int"
            size_hint_x: 0.25

        MDRaisedButton:
            id: btn_conectar
            text: "Conectar"
            size_hint_x: 0.30
            pos_hint: {"center_y": 0.5}
            on_release: app.alternar_conexao()

    MDLabel:
        id: conn_status_label
        text: "Conexão: Desconectado"
        halign: "center"
        theme_text_color: "Secondary"
        size_hint_y: None
        height: dp(25)

    # --- Seletor de Tipo de Dado (As 4 opções exigidas) ---
    MDLabel:
        text: "Tipo de Operação / Dado:"
        size_hint_y: None
        height: dp(20)

    Spinner:
        id: type_spinner
        text: "Holding Register"
        values: ("Holding Register", "Coil", "Float", "Bits de Registrador")
        size_hint_y: None
        height: dp(44)

    # --- Campos de Endereço, Bits e Valor ---
    MDBoxLayout:
        orientation: 'horizontal'
        spacing: dp(10)
        size_hint_y: None
        height: dp(60)

        MDTextField:
            id: addr_field
            text: "700"
            hint_text: "Endereço (ex: 700, 1328)"
            input_filter: "int"
            size_hint_x: 0.5

        MDTextField:
            id: bit_field
            hint_text: "Bit(s) (ex: 6 ou 0,1,6)"
            size_hint_x: 0.5

    MDTextField:
        id: value_field
        hint_text: "Valor para Escrever (ex: 100, 65.5, True, ou 1,0,1 p/ bits)"
        size_hint_y: None
        height: dp(60)

    # --- Botões Ler e Escrever ---
    MDBoxLayout:
        orientation: 'horizontal'
        spacing: dp(15)
        size_hint_y: None
        height: dp(50)

        MDRaisedButton:
            text: "Ler Dados"
            size_hint_x: 0.5
            on_release: app.ler_dados()

        MDRaisedButton:
            text: "Escrever Dados"
            size_hint_x: 0.5
            on_release: app.escrever_dados()

    # --- Resultado / Status ---
    MDLabel:
        id: status_label
        text: "Resultado: Aguardando operação..."
        halign: "center"
        theme_text_color: "Primary"

    Widget:
'''


class ModbusGUIApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.modbus = ClienteMODBUS()
        return Builder.load_string(KV)

    def alternar_conexao(self):
        """Lê IP e Porta digitados na interface e conecta ou desconecta."""
        if not self.modbus.conectado:
            ip = self.root.ids.ip_field.text.strip() or "localhost"
            porta_str = self.root.ids.port_field.text.strip() or "502"

            self.modbus.configurar_conexao(ip, int(porta_str))
            if self.modbus.conectar():
                self.root.ids.conn_status_label.text = f"Conexão: Conectado em {ip}:{porta_str}"
                self.root.ids.btn_conectar.text = "Desconectar"
                self.root.ids.status_label.text = "Resultado: Conectado com sucesso!"
            else:
                self.root.ids.conn_status_label.text = f"Conexão: Falha ({ip}:{porta_str})"
                self.root.ids.status_label.text = "Resultado: Erro ao conectar ao servidor."
        else:
            self.modbus.desconectar()
            self.root.ids.conn_status_label.text = "Conexão: Desconectado"
            self.root.ids.btn_conectar.text = "Conectar"
            self.root.ids.status_label.text = "Resultado: Desconectado."

    def ler_dados(self):
        """Chama os métodos de leitura da classe ClienteMODBUS conforme o tipo selecionado."""
        if not self.modbus.conectado:
            self.root.ids.status_label.text = "Resultado: Conecte ao servidor primeiro!"
            return

        addr_str = self.root.ids.addr_field.text.strip()
        if not addr_str:
            self.root.ids.status_label.text = "Resultado: Informe um endereço válido!"
            return

        addr = int(addr_str)
        tipo = self.root.ids.type_spinner.text
        bits_str = self.root.ids.bit_field.text.strip()

        if tipo == "Holding Register":
            res = self.modbus.ler_holding_registers(addr, count=1)
            texto = f"Holding Reg [{addr}]: {res[0]}" if res else "Erro na leitura"
        elif tipo == "Coil":
            res = self.modbus.ler_coils(addr, count=1)
            texto = f"Coil [{addr}]: {res[0]}" if res is not None else "Erro na leitura"
        elif tipo == "Float":
            res = self.modbus.ler_float(addr)
            texto = f"Float [{addr}]: {res}" if res is not None else "Erro na leitura"
        elif tipo == "Bits de Registrador":
            res = self.modbus.ler_bits(addr, bits_str)
            texto = f"Bits [{addr}]: {res}" if res is not None else "Erro na leitura dos bits"
        else:
            texto = "Tipo inválido"

        self.root.ids.status_label.text = f"Resultado: {texto}"

    def escrever_dados(self):
        """Chama os métodos de escrita da classe ClienteMODBUS conforme o tipo selecionado."""
        if not self.modbus.conectado:
            self.root.ids.status_label.text = "Resultado: Conecte ao servidor primeiro!"
            return

        addr_str = self.root.ids.addr_field.text.strip()
        val_str = self.root.ids.value_field.text.strip()
        bits_str = self.root.ids.bit_field.text.strip()

        if not addr_str or not val_str:
            self.root.ids.status_label.text = "Resultado: Informe endereço e valor!"
            return

        addr = int(addr_str)
        tipo = self.root.ids.type_spinner.text
        sucesso = False

        if tipo == "Holding Register":
            sucesso = self.modbus.escrever_holding_register(addr, val_str)
        elif tipo == "Coil":
            sucesso = self.modbus.escrever_coil(addr, val_str)
        elif tipo == "Float":
            sucesso = self.modbus.escreve_float(addr, val_str)
        elif tipo == "Bits de Registrador":
            # Se digitou apenas 1 bit sem vírgula, usa escreve_bit; se múltiplos, usa escreve_multiplos_bits
            if bits_str and "," not in bits_str and "," not in val_str:
                sucesso = self.modbus.escreve_bit(addr, bits_str, val_str)
            else:
                sucesso = self.modbus.escreve_multiplos_bits(addr, bits_str, val_str)

        msg = f"Escrita em [{addr}] concluída com sucesso!" if sucesso else "Erro ao escrever dados."
        self.root.ids.status_label.text = f"Resultado: {msg}"


if __name__ == '__main__':
    ModbusGUIApp().run()