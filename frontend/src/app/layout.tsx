import type {Metadata} from "next";import "./globals.css";import {Shell} from "@/components/Shell";
export const metadata:Metadata={title:"DiagPilot — Diagnostic guidé",description:"MVP fictif d’assistance au diagnostic automobile"};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="fr"><body><Shell>{children}</Shell></body></html>}

