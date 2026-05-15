import "./globals.css";

export const metadata = {
  title: "ERP Guardian AI - Dashboard",
  description: "Autonomous ERP Software Factory Control Center",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-br">
      <body>{children}</body>
    </html>
  );
}
