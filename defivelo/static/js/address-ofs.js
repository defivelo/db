function selectedDataAutocomplete() {
  $("#id_address_city_autocomplete").on("select2:select", function (e) {
    const selectedData = e.params.data;
    $("#id_address_ofs_no").val(selectedData.id);

    // Save City and Canton separately
    const label = selectedData.text;
    const regex = /(^.*)( \(([A-Z]{2})\))$/;
    const matches = label.match(regex);
    if (matches) {
      console.log("Update state to: ", matches[3])
      $("#id_address_city").val(matches[1]);
      $("#id_address_canton").val(matches[3]);
    } else {
      $("#id_address_city").val(label)
    }
  });
}

function toggleAddressFields() {
  const countryField = document.getElementById('id_address_country');
  const cityAutoContainer = document.getElementById('address_city_auto_container');
  const cityContainer = document.getElementById('address_city_container');
  const isSwitzerland = countryField.value === 'CH';

  if (isSwitzerland) {
    // Display City autocomplete group (city + state + ofs)
    cityAutoContainer.style.display = 'block';

    // Clean & Hide City free field
    $("#id_address_city").val("");
    cityContainer.style.display = 'none';

  } else {
    // Clean & Hide City autocomplete group (city + state + ofs)
    $("#id_address_canton").val("");
    $("#id_address_ofs_no").val("");
    cityAutoContainer.style.display = 'none';

    // Display City free field
    cityContainer.style.display = 'block';
  }
}

function initAddressAutocompleteField($autocompleteField) {
  /**
   * Try to fill the autocomplete field with a default value, before the first request to the OFS API.
   **/
  const initialValOfs = $("#id_address_ofs_no").val() | 0;
  const initialValLabel = $("#id_address_city").val();
  console.log("YES", initialValLabel, initialValOfs);
  if (initialValLabel) {
    const $option = $("<option selected></option>").val(initialValOfs).text(initialValLabel);
    $autocompleteField.append($option).trigger('change');
  }
}

document.addEventListener("DOMContentLoaded", function () {
  // Display an initial value in the autocomplete OFS Field
  const $autocompleteField = $('#id_address_city_autocomplete');
  initAddressAutocompleteField($autocompleteField)

  // Register change callback
  $autocompleteField.change(selectedDataAutocomplete);

  // Display address fields depending on the Country
  const countryField = document.getElementById('id_address_country');
  countryField.addEventListener('change', toggleAddressFields);
  toggleAddressFields();
});
