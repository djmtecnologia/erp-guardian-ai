unit UGeradorPedido;

interface

uses
  System.SysUtils, System.Classes, Data.DB, OracleData;

type
  TFormPedido = class(TForm)
    qryPedido: TOracleDataSet;
    procedure btnSalvarClick(Sender: TObject);
  private
    { Private declarations }
  public
    { Public declarations }
  end;

var
  FormPedido: TFormPedido;

implementation

{$R *.dfm}

procedure TFormPedido.btnSalvarClick(Sender: TObject);
var
  Total: Double;
begin
  //Derik Moretti da Silveira -
  // Simulação de erro de leak e falta de transação
  Total := 100.50;
  qryPedido.SQL.Text := 'INSERT INTO PEDIDOS (VALOR) VALUES (' + FloatToStr(Total) + ')';
  qryPedido.Execute;
  // Faltou Commit
end;

end.
