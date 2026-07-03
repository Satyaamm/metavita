import { redirect } from "next/navigation";

// Provider keys now live in the unified Connections page — this legacy route just
// forwards there so there's a single place to manage every integration.
export default function ProvidersRedirect() {
  redirect("/connections");
}
