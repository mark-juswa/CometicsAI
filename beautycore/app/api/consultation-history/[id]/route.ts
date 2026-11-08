import { consultationHistory } from '@/lib/business/customer-history';
import { historyDependencies } from '@/lib/business/history-server';
export async function GET(request:Request,context:{params:Promise<{id:string}>}){
 return consultationHistory(request,historyDependencies,(await context.params).id);
}
