import { consultationHistory } from '@/lib/business/customer-history';
import { historyDependencies } from '@/lib/business/history-server';
export const GET=(request:Request)=>consultationHistory(request,historyDependencies);
