import { workAvailability } from '@/lib/business/work-availability';
import { historyDependencies } from '@/lib/business/history-server';
export const GET=(request:Request)=>workAvailability(request,historyDependencies);
export const PUT=GET;
