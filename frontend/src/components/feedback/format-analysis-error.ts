export const formatAnalysisError = (
  error: string | null | undefined
): string => {
  if (error?.startsWith("Provider output schema validation failed"))
    return "The AI response did not match the required format. Try again.";
  if (error?.startsWith("Provider evidence validation failed"))
    return "The AI quotes did not match the original message. Try again.";

  switch (error) {
    case "Provider response envelope validation failed":
      return "The AI service returned an unreadable response. Try again.";
    case "Provider output exceeds 8192 characters":
      return "The AI response was too long to process. Try again.";
  }

  if (error?.includes("budget exhausted"))
    return "The AI request limit for this demo has been reached.";
  if (error?.includes("(402)"))
    return "The AI service has no available credits. Add credits before trying again.";
  if (error?.includes("(401)"))
    return "The AI service could not authenticate. Its server credentials need to be updated.";
  if (error?.includes("validation"))
    return "The AI response could not be verified against the original message. Try again.";
  if (error?.includes("timed out") || error === "TimeoutError")
    return "The AI service took too long to respond. Try again.";

  return "The AI service couldn’t complete the request. Try again; your message and previous result are safe.";
};
