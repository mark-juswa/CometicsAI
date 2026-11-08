import { clientHistory } from '@/lib/business/customer-history';
import { historyDependencies } from '@/lib/business/history-server';
export async function GET(request:Request,context:{params:Promise<{id:string}>}){
 return clientHistory(request,(await context.params).id,historyDependencies);
}
