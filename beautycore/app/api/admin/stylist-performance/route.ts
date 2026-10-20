import { stylistPerformance } from '../../../../lib/business/api';
import { businessDependencies } from '../../../../lib/business/server';
export const dynamic = 'force-dynamic';
export const GET = (request: Request) => stylistPerformance(request, businessDependencies);
