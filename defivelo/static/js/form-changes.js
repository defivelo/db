function trackFormChanges(formSelector) {
    const $form = $(formSelector);
    const initialData = $form.serialize();
    let isDirty = false;

    $form.on('change input', () => {
        isDirty = $form.serialize() !== initialData;
    });

    $(window).on('beforeunload', (e) => {
        if (isDirty) {
            return e.originalEvent.returnValue = "You have unsaved changes!";
        }
    });

    // Optional: reset tracking after successful save
    $form.on('submit', () => {
        isDirty = false;
    });
}

$(document).ready(function() {
  $('form[data-prevent-page-exit]').each(function() {
    trackFormChanges(this);
  });
});
