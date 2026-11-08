import { ClientHistory } from '@/components/client-history';
export default async function Page({params}:{params:Promise<{id:string}>}){return <ClientHistory clientId={(await params).id}/>;}
