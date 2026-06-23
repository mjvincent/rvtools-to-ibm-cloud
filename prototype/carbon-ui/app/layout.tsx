import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import '@carbon/styles/css/styles.css';
import './styles.css';

export const metadata: Metadata = {
  title: 'RVTools to IBM Cloud Prototype',
  description: 'Experimental Carbon UI for RVTools migration planning.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
