window.createLiveSaveIndicator = function createLiveSaveIndicator(element) {
  if (!element) {
    return {
      setSaving() {},
      setSaved() {},
      setError() {},
    };
  }

  function renderSaved() {
    element.innerHTML = 'Saved <span data-feather="check" class="align-text-bottom ms-1"></span>';
    if (window.feather) {
      window.feather.replace({ width: '1em', height: '1em' });
    }
  }

  return {
    setSaving() {
      element.classList.add('live-save-pending');
      element.classList.remove('text-danger');
      element.textContent = 'Saving...';
    },
    setSaved() {
      element.classList.remove('live-save-pending');
      element.classList.remove('text-danger');
      renderSaved();
    },
    setError() {
      element.classList.remove('live-save-pending');
      element.classList.add('text-danger');
      element.textContent = 'Save failed';
    },
  };
};
