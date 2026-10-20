import { appointmentReview } from '../../../../../lib/business/api';
import { businessDependencies } from '../../../../../lib/business/server';
export const dynamic = 'force-dynamic';
export const POST = async (request: Request, context: { params: Promise<{ id: string }> }) =>
  appointmentReview(request, (await context.params).id, businessDependencies);
