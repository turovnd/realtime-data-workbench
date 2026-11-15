import { PageMessage } from "@/components/layout";
import { Button } from "@/components/ui";

import { Path } from "./paths";

export const RouteError = () => (
  <PageMessage
    title="We couldn’t open this page"
    description="Reload the page to try again, or return to your inbox."
    backTo={Path.Feedback}
  >
    <Button variant="outline" onClick={() => window.location.reload()}>
      Reload page
    </Button>
  </PageMessage>
);
