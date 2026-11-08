import { ConsultationHistory } from '@/components/consultation-history';
export default async function Page({params}:{params:Promise<{id:string}>}){return <ConsultationHistory sessionId={(await params).id}/>;}
