import { paymentHistory } from '@/lib/business/customer-history';
import { historyDependencies } from '@/lib/business/history-server';
export const GET=(request:Request)=>paymentHistory(request,historyDependencies);
