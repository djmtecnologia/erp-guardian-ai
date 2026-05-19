; Script de Instalação do ERP Guardian Agent para Usuários Limitados (Sem Admin)
; Criado para ERP Guardian AI Factory

[Setup]
AppName=ERP Guardian Agent
AppVersion=1.2.0
DefaultDirName={localappdata}\Programs\ERPGuardianAgent
DefaultGroupName=ERP Guardian Agent
OutputBaseFilename=ERPGuardianAgent_Setup
Compression=lzma
SolidCompression=yes
; ESSENCIAL: Diz ao Inno Setup para NÃO pedir senha de administrador
PrivilegesRequired=lowest
OutputDir=.\dist

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos Adicionais:"; Flags: unchecked

[Files]
; Inclui os arquivos gerados pelo PyInstaller na pasta 'dist\ERPGuardianAgent'
Source: "dist\ERPGuardianAgent\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\ERP Guardian Agent"; Filename: "{app}\ERPGuardianAgent.exe"
Name: "{userdesktop}\ERP Guardian Agent"; Filename: "{app}\ERPGuardianAgent.exe"; Tasks: desktopicon

[Run]
; Executa o Agente logo após a instalação terminar, sob o contexto do usuário comum
Filename: "{app}\ERPGuardianAgent.exe"; Description: "Iniciar ERP Guardian Agent"; Flags: nowait postinstall skipifsilent

[Code]
procedure CreateEnvFileIfMissing();
var
  EnvPath: String;
  EnvContent: TStringList;
begin
  EnvPath := ExpandConstant('{app}\.env');
  if not FileExists(EnvPath) then
  begin
    EnvContent := TStringList.Create;
    try
      EnvContent.Add('# ERP Guardian AI - Configuracao do Agente Local');
      EnvContent.Add('# Preencha as chaves abaixo para ativar os recursos de IA e nuvem.');
      EnvContent.Add('');
      EnvContent.Add('# Chave da API do Google Gemini (obrigatorio para analise de codigo)');
      EnvContent.Add('GEMINI_API_KEY=');
      EnvContent.Add('');
      EnvContent.Add('# URL do backend na nuvem (padrao ja configurado para a Vercel)');
      EnvContent.Add('BACKEND_URL=https://erp-guardian-ai.vercel.app');
      EnvContent.Add('');
      EnvContent.Add('# Caminho local do diretorio de VCS a monitorar (opcional)');
      EnvContent.Add('# LOCAL_VCS_PATH=C:\ERP\Fontes');
      EnvContent.SaveToFile(EnvPath);
    finally
      EnvContent.Free;
    end;
    MsgBox('Um arquivo .env foi criado em ' + EnvPath + #13#10 +
           'Abra-o com o Bloco de Notas e preencha o campo GEMINI_API_KEY.', 
           mbInformation, MB_OK);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    CreateEnvFileIfMissing();
end;
