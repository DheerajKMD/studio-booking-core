from apps.common.exceptions import DomainError


class ClassNotFound(DomainError):
    status_code = 404
    code = "class_not_found"


class ClassFull(DomainError):
    status_code = 409
    code = "class_full"


class ClassAlreadyStarted(DomainError):
    status_code = 409
    code = "class_already_started"


class AlreadyBooked(DomainError):
    status_code = 409
    code = "already_booked"


class BookingNotFound(DomainError):
    status_code = 404
    code = "booking_not_found"


class ClassNotFull(DomainError):
    status_code = 409
    code = "class_not_full"


class AlreadyWaitlisted(DomainError):
    status_code = 409
    code = "already_waitlisted"


class WaitlistEntryNotFound(DomainError):
    status_code = 404
    code = "waitlist_entry_not_found"
