#!/bin/bash
# Creates HSN SAC entries one by one via agent-browser

entries=(
  "0201|Commodity|Meat of bovine animals fresh or chilled"
  "0301|Commodity|Live fish and aquatic invertebrates"
  "0401|Commodity|Milk and cream not concentrated nor sweetened"
  "0501|Commodity|Human hair unworked whether or not washed"
  "0601|Commodity|Bulbs tubers corms and rhizomes dormant"
  "0701|Commodity|Potatoes fresh or chilled"
  "0801|Commodity|Coconuts Brazil nuts and cashew nuts fresh"
  "0901|Commodity|Coffee whether or not roasted or decaffeinated"
  "1001|Commodity|Wheat and meslin"
  "995413|Services|Installation services of prefabricated structures"
  "995414|Services|Building completion and finishing services"
  "995415|Services|Building installation services plumbing and electrical"
  "996311|Services|Food and beverage serving services with waiter service"
  "996312|Services|Catering services for events and functions"
  "997111|Commission|Commission on sale of agricultural products"
  "997112|Commission|Commission on purchase of raw materials"
  "997113|Commission|Commission on sale of manufactured goods"
  "996211|Transportation|Road transport services for goods by motor vehicles"
  "996212|Transportation|Railway freight transport services for goods"
)

success=0
fail=0

for entry in "${entries[@]}"; do
  IFS='|' read -r number type desc <<< "$entry"
  echo "Creating: $number - $type - $desc"
  
  # Click Add button
  agent-browser eval "
    var btns = document.querySelectorAll('button');
    var addBtn = null;
    for(var i=0;i<btns.length;i++){
      if(btns[i].textContent.includes('Add HSN SAC')){
        addBtn = btns[i]; break;
      }
    }
    if(addBtn) { addBtn.click(); 'ok'; } else { 'no add btn'; }
  " 2>&1 | tail -1
  
  sleep 1.5
  
  # Fill HSN SAC Number
  agent-browser eval "
    var inputs = document.querySelectorAll('input');
    var numberInput = null;
    for(var i=0;i<inputs.length;i++){
      var placeholder = inputs[i].getAttribute('placeholder') || '';
      var id = inputs[i].id || '';
      var name = inputs[i].getAttribute('name') || '';
      if(placeholder.toLowerCase().includes('number') || id.toLowerCase().includes('number') || name.toLowerCase().includes('number')){
        numberInput = inputs[i]; break;
      }
    }
    // Fallback: first input in dialog/form
    if(!numberInput) {
      var formInputs = document.querySelectorAll('mat-dialog-container input, .mat-card input, form input');
      if(formInputs.length > 0) numberInput = formInputs[0];
    }
    if(numberInput) {
      var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(numberInput, '$number');
      numberInput.dispatchEvent(new Event('input', {bubbles: true}));
      numberInput.dispatchEvent(new Event('change', {bubbles: true}));
      'filled number: $number';
    } else {
      'number input not found';
    }
  " 2>&1 | tail -1
  
  sleep 0.5
  
  # Select HSN SAC Type
  agent-browser eval "
    // Click the mat-select trigger
    var selects = document.querySelectorAll('mat-select');
    var typeSelect = null;
    for(var i=0;i<selects.length;i++){
      var label = selects[i].querySelector('mat-label, .mat-select-placeholder, span');
      if(label && (label.textContent.includes('Type') || label.textContent.includes('type'))){
        typeSelect = selects[i]; break;
      }
    }
    if(!typeSelect && selects.length > 0) typeSelect = selects[0];
    if(typeSelect) {
      typeSelect.click();
      typeSelect.dispatchEvent(new Event('click', {bubbles: true}));
      'opened type select';
    } else {
      'type select not found';
    }
  " 2>&1 | tail -1
  
  sleep 0.8
  
  # Select the type option
  agent-browser eval "
    var options = document.querySelectorAll('mat-option');
    var selected = false;
    for(var i=0;i<options.length;i++){
      if(options[i].textContent.trim() === '$type'){
        options[i].click();
        selected = true;
        break;
      }
    }
    selected ? 'selected $type' : 'option $type not found, available: ' + Array.from(options).map(o=>o.textContent.trim()).join(',');
  " 2>&1 | tail -1
  
  sleep 0.5
  
  # Fill Description
  agent-browser eval "
    var inputs = document.querySelectorAll('input, textarea');
    var descInput = null;
    for(var i=0;i<inputs.length;i++){
      var placeholder = inputs[i].getAttribute('placeholder') || '';
      var id = inputs[i].id || '';
      var name = inputs[i].getAttribute('name') || '';
      if(placeholder.toLowerCase().includes('desc') || id.toLowerCase().includes('desc') || name.toLowerCase().includes('desc')){
        descInput = inputs[i]; break;
      }
    }
    // Fallback: second input in dialog
    if(!descInput) {
      var formInputs = document.querySelectorAll('mat-dialog-container input, .mat-card input, form input');
      if(formInputs.length > 1) descInput = formInputs[1];
    }
    if(descInput) {
      var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(descInput, '$desc');
      descInput.dispatchEvent(new Event('input', {bubbles: true}));
      descInput.dispatchEvent(new Event('change', {bubbles: true}));
      'filled desc';
    } else {
      'desc input not found';
    }
  " 2>&1 | tail -1
  
  sleep 0.5
  
  # Click Submit
  agent-browser eval "
    var btns = document.querySelectorAll('button');
    var submitBtn = null;
    for(var i=0;i<btns.length;i++){
      if(btns[i].textContent.trim() === 'Submit'){
        submitBtn = btns[i]; break;
      }
    }
    if(submitBtn) { submitBtn.click(); 'submitted'; } else { 'submit not found'; }
  " 2>&1 | tail -1
  
  sleep 3
  
  # Check result
  result=$(agent-browser eval "
    var swal = document.querySelector('.swal2-title');
    if(swal) {
      swal.textContent.trim();
    } else {
      var popup = document.querySelector('.swal2-container');
      if(popup) 'popup visible but no title';
      else 'no popup - likely success or form still open';
    }
  " 2>&1 | tail -1)
  
  echo "  Result: $result"
  
  # Dismiss any swal popup
  agent-browser eval "
    var confirmBtn = document.querySelector('.swal2-confirm');
    if(confirmBtn) { confirmBtn.click(); 'dismissed'; } else { 'no swal to dismiss'; }
  " 2>&1 > /dev/null
  
  sleep 1
  
  # Verify entry was added
  count=$(agent-browser eval "
    var rows = document.querySelectorAll('table tbody tr, mat-row');
    rows.length.toString();
  " 2>&1 | tail -1)
  
  echo "  Table rows: $count"
  
done

echo "Done!"
