import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from clientemodbus import ClienteMODBUS

Window.size = (500, 700)

KV = '''
MDBoxLayout:
    orientation: 'vertical'
    padding: dp(20)
    spacing: dp(10)

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

    # --- Seletor de Tipo de Dado 100% KivyMD (MDDropdownMenu) ---
    MDBoxLayout:
        orientation: 'horizontal'
        spacing: dp(10)
        size_hint_y: None
        height: dp(50)

        MDLabel:
            text: "Tipo de Dado:"
            size_hint_x: 0.4
            pos_hint: {"center_y": 0.5}

        MDRaisedButton:
            id: btn_tipo
            text: "Holding Register"
            size_hint_x: 0.6
            pos_hint: {"center_y": 0.5}
            on_release: app.menu_tipos.open()

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

    # --- Checkbox de Leitura Recorrente ---
    MDBoxLayout:
        orientation: 'horizontal'
        spacing: dp(10)
        size_hint_y: None
        height: dp(40)

        MDCheckbox:
            id: chk_recorrente
            size_hint: None, None
            size: dp(40), dp(40)
            pos_hint: {'center_y': 0.5}
            on_active: app.alternar_leitura_recorrente(self, self.active)

        MDLabel:
            text: "Leitura Recorrente Automática (a cada 1s)"
            pos_hint: {'center_y': 0.5}

    # --- Botões Ler e Escrever ---
    MDBoxLayout:
        orientation: 'horizontal'
        spacing: dp(15)
        size_hint_y: None
        height: dp(50)

        MDRaisedButton:
            text: "Ler Dados"
            size_hint_x: 0.5
            on_release: app.acao_botao_ler()

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
        self.evento_leitura = None
        self.tipo_selecionado = "Holding Register"
        root = Builder.load_string(KV)

        # Cria o menu dropdown nativo do KivyMD com as 4 opções exigidas
        opcoes = ["Holding Register", "Coil", "Float", "Bits de Registrador"]
        itens_menu = [
            {
                "text": opcao,
                "viewclass": "OneLineListItem",
                "height": dp(48),
                "on_release": lambda x=opcao: self.selecionar_tipo(x),
            }
            for opcao in opcoes
        ]
        self.menu_tipos = MDDropdownMenu(
            caller=root.ids.btn_tipo,
            items=itens_menu,
            width_mult=4,
        )
        return root

    def selecionar_tipo(self, tipo):
        self.tipo_selecionado = tipo
        self.root.ids.btn_tipo.text = tipo
        self.menu_tipos.dismiss()

    def alternar_conexao(self):
        """Apenas repassa IP e Porta da GUI para a classe ClienteMODBUS."""
        if not self.modbus.conectado:
            ip = self.root.ids.ip_field.text.strip() or "localhost"
            porta = self.root.ids.port_field.text.strip() or "502"

            self.modbus.configurar_conexao(ip, porta)
            if self.modbus.conectar():
                self.root.ids.conn_status_label.text = f"Conexão: Conectado em {ip}:{porta}"
                self.root.ids.btn_conectar.text = "Desconectar"
                self.root.ids.status_label.text = "Resultado: Conectado com sucesso!"
            else:
                self.root.ids.conn_status_label.text = f"Conexão: Falha ({ip}:{porta})"
                self.root.ids.status_label.text = "Resultado: Erro ao conectar ao servidor."
        else:
            self.parar_leitura_recorrente()
            self.root.ids.chk_recorrente.active = False

            self.modbus.desconectar()
            self.root.ids.conn_status_label.text = "Conexão: Desconectado"
            self.root.ids.btn_conectar.text = "Conectar"
            self.root.ids.status_label.text = "Resultado: Desconectado."

    def alternar_leitura_recorrente(self, checkbox, valor_ativo):
        if valor_ativo:
            if not self.modbus.conectado:
                self.root.ids.status_label.text = "Resultado: Conecte ao servidor antes de ativar a leitura recorrente!"
                checkbox.active = False
                return
            self.iniciar_leitura_recorrente()
        else:
            self.parar_leitura_recorrente()

    def iniciar_leitura_recorrente(self):
        self.parar_leitura_recorrente()
        self.ler_dados()
        self.evento_leitura = Clock.schedule_interval(self._ciclo_leitura, 1.0)

    def parar_leitura_recorrente(self):
        if self.evento_leitura is not None:
            self.evento_leitura.cancel()
            self.evento_leitura = None

    def _ciclo_leitura(self, dt):
        if not self.modbus.conectado:
            self.parar_leitura_recorrente()
            self.root.ids.chk_recorrente.active = False
            return
        self.ler_dados()

    def acao_botao_ler(self):
        if self.root.ids.chk_recorrente.active:
            self.iniciar_leitura_recorrente()
        else:
            self.ler_dados()

    def ler_dados(self):
        """Apenas chama os métodos de leitura da classe ClienteMODBUS."""
        if not self.modbus.conectado:
            self.root.ids.status_label.text = "Resultado: Conecte ao servidor primeiro!"
            return

        addr_str = self.root.ids.addr_field.text.strip()
        if not addr_str:
            self.root.ids.status_label.text = "Resultado: Informe um endereço válido!"
            return

        tipo = self.tipo_selecionado
        bits_str = self.root.ids.bit_field.text.strip()
        modo = "[Recorrente] " if self.root.ids.chk_recorrente.active else ""

        if tipo == "Holding Register":
            res = self.modbus.ler_holding_registers(addr_str, count=1)
            texto = f"Holding Reg [{addr_str}]: {res[0]}" if res else "Erro na leitura"
        elif tipo == "Coil":
            res = self.modbus.ler_coils(addr_str, count=1)
            texto = f"Coil [{addr_str}]: {res[0]}" if res is not None else "Erro na leitura"
        elif tipo == "Float":
            res = self.modbus.ler_float(addr_str)
            texto = f"Float [{addr_str}]: {res}" if res is not None else "Erro na leitura"
        elif tipo == "Bits de Registrador":
            res = self.modbus.ler_bits(addr_str, bits_str)
            texto = f"Bits [{addr_str}]: {res}" if res is not None else "Erro na leitura dos bits"
        else:
            texto = "Tipo inválido"

        self.root.ids.status_label.text = f"Resultado: {modo}{texto}"

    def escrever_dados(self):
        """Apenas chama os métodos de escrita da classe ClienteMODBUS."""
        if not self.modbus.conectado:
            self.root.ids.status_label.text = "Resultado: Conecte ao servidor primeiro!"
            return

        addr_str = self.root.ids.addr_field.text.strip()
        val_str = self.root.ids.value_field.text.strip()
        bits_str = self.root.ids.bit_field.text.strip()

        if not addr_str or not val_str:
            self.root.ids.status_label.text = "Resultado: Informe endereço e valor!"
            return

        tipo = self.tipo_selecionado
        sucesso = False

        if tipo == "Holding Register":
            sucesso = self.modbus.escrever_holding_register(addr_str, val_str)
        elif tipo == "Coil":
            sucesso = self.modbus.escrever_coil(addr_str, val_str)
        elif tipo == "Float":
            sucesso = self.modbus.escreve_float(addr_str, val_str)
        elif tipo == "Bits de Registrador":
            sucesso = self.modbus.escreve_multiplos_bits(addr_str, bits_str, val_str)

        msg = f"Escrita em [{addr_str}] concluída com sucesso!" if sucesso else "Erro ao escrever dados."
        self.root.ids.status_label.text = f"Resultado: {msg}"


if __name__ == '__main__':
    ModbusGUIApp().run()