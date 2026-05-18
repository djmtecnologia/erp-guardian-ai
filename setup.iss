; Script de Instalação do ERP Guardian Agent para Usuários Limitados (Sem Admin)
; Criado para ERP Guardian AI Factory

[Setup]
AppName=ERP Guardian Agent
AppVersion=1.0.0
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
