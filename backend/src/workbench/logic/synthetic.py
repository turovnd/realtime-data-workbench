from workbench.schemas.feedback import FeedbackInput

SAMPLES = (
    ("The activity page loses my filters whenever new updates arrive.", "In-app"),
    ("CSV export times out when I select the full month of feedback.", "Support"),
    ("Please add a keyboard shortcut to jump between saved views.", "Community"),
    ("The billing page charged our workspace twice this month.", "Support"),
    ("Search feels slow when I paste a long customer reference.", "In-app"),
    ("The new filters make our weekly review much easier. Thank you!", "Community"),
    ("Notifications stop arriving after I reconnect to the network.", "Support"),
    ("Please let me pin the source column in the feedback table.", "In-app"),
    ("The invoice download button returns an empty document.", "Support"),
    ("The dashboard takes ten seconds to load on my laptop.", "In-app"),
    ("The new evidence panel makes the original feedback easy to verify.", "Community"),
    ("Something changed yesterday, but I cannot tell what it was.", "Community"),
)


def synthetic_inputs(request_id: str, count: int) -> list[FeedbackInput]:
    return [
        FeedbackInput.model_validate(
            {
                "identity": f"{request_id}:{index}",
                "text": SAMPLES[index][0],
                "channel": SAMPLES[index][1],
            }
        )
        for index in range(count)
    ]
