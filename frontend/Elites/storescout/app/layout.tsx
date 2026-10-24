import type {Metadata} from 'next';
import '@fontsource-variable/manrope';
import './globals.css';
export const metadata:Metadata={metadataBase:new URL('https://storescout-retail-atlas.suregleam65.chatgpt.site'),title:'StoreScout — Find where growth creates value.',description:'Explore a new perspective on retail expansion. StoreScout connects location evidence, DaypartDNA, FailFast and portfolio thinking in an illustrative investment journey.',openGraph:{title:'StoreScout — A better place to grow.',description:'Retail expansion intelligence. From opportunity to investment value.',type:'website'}};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
