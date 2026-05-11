"""Redis Streams topic names for the HireFlow agent pipeline."""


class Topics:
    JD_APPROVED = "hireflow:jd:approved"
    DISTRIBUTION_STARTED = "hireflow:distribution:started"
    CHANNEL_POSTED = "hireflow:channel:posted"         # per-channel events share one stream
    APPLICATION_RECEIVED = "hireflow:application:received"
    CV_PARSED = "hireflow:cv:parsed"
    SCORING_COMPLETE = "hireflow:scoring:complete"
    SHORTLIST_READY = "hireflow:shortlist:ready"
    PERSONA_ALERT = "hireflow:persona:alert"
    AGENT_ERROR = "hireflow:agent:error"               # dead-letter stream

    # Consumer group names
    GROUP_WORKER = "hireflow-worker"
    GROUP_NOTIFIER = "hireflow-notifier"
