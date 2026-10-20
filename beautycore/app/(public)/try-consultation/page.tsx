import Link from "next/link";
import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth";
import Consultation from "@/components/consultation";
export const dynamic = "force-dynamic";
export default async function TrialPage() {
  const session = await getSession();
  if (session)
    redirect(
      session.role === "client"
        ? "/client/ai-consultation"
        : "/" + session.role + "/dashboard",
    );
  if (process.env.AI_GUEST_TRIAL_ENABLED !== "true")
    return (
      <section className="mx-auto max-w-3xl px-6 py-20">
        <h1 className="font-serif text-4xl">AI consultation</h1>
        <p className="my-6">
          The guest trial is currently unavailable. Log in or create an account
          for the full consultation.
        </p>
        <Link href="/register?continue=consultation">Create an account</Link>
        {" Â· "}
        <Link href="/login?continue=consultation">Log in</Link>
      </section>
    );
  return <Consultation trial />;
}
