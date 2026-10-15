document.addEventListener('DOMContentLoaded', async () => {
  const showdownFrame = document.getElementById('showdownFrame');
  const btnStart = document.getElementById('btnStart');
  const winnerOutput = document.getElementById('winnerOutput');
  const btnShowError = document.getElementById('btnShowError');
  const errorModal = document.getElementById('errorModal');
  const errorDetails = document.getElementById('errorDetails');
  const btnCloseError = document.getElementById('btnCloseError');

  const p1Selects = [
    document.getElementById('p1_poke1'),
    document.getElementById('p1_poke2'),
    document.getElementById('p1_poke3')
  ];

  const p2Selects = [
    document.getElementById('p2_poke1'),
    document.getElementById('p2_poke2'),
    document.getElementById('p2_poke3')
  ];

  const p1SlotsContainer = document.getElementById('p1_custom_slots');
  const p2SlotsContainer = document.getElementById('p2_custom_slots');

  const p1FileInput = document.getElementById('p1_file');
  const p2FileInput = document.getElementById('p2_file');
  const p1SampleSelect = document.getElementById('p1Sample');
  const p2SampleSelect = document.getElementById('p2Sample');

  // Toggle customization buttons
  document.querySelectorAll('.btn-toggle-custom').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      const target = document.getElementById(targetId);
      if (target) {
        target.classList.toggle('hidden');
        btn.classList.toggle('active');
      }
    });
  });

  // State
  let pokemonDb = {};
  let itemsList = [];
  let naturesList = [];
  let evPresetsList = [];

  const defaultP1 = ['Garchomp', 'Metagross', 'Volcarona'];
  const defaultP2 = ['Dragonite', 'Tyranitar', 'Scizor'];

  let teamP1 = [];
  let teamP2 = [];

  // Fetch full Pokemon options
  try {
    const res = await fetch('/api/pokemon-options');
    const data = await res.json();
    if (data.success) {
      pokemonDb = data.pokemon || {};
      itemsList = data.items || [];
      naturesList = data.natures || [];
      evPresetsList = data.evPresets || [];

      initTeams();
    }
  } catch (err) {
    console.error('Failed to load pokemon options:', err);
  }

  function initTeams() {
    const rosterNames = Object.keys(pokemonDb);

    // Initialize team arrays
    teamP1 = defaultP1.map(name => createDefaultPokeConfig(name));
    teamP2 = defaultP2.map(name => createDefaultPokeConfig(name));

    // Populate top-level selects
    const formatOption = (name) => {
      const p = pokemonDb[name];
      const typeStr = p ? ` [${p.types.join('/')}]` : '';
      return `<option value="${name}">${name}${typeStr}</option>`;
    };

    const optionsHtml = rosterNames.map(formatOption).join('');

    p1Selects.forEach((sel, idx) => {
      sel.innerHTML = optionsHtml;
      sel.value = defaultP1[idx] || rosterNames[0];
      sel.addEventListener('change', () => onPokeChange('p1', idx, sel.value));
    });

    p2Selects.forEach((sel, idx) => {
      sel.innerHTML = optionsHtml;
      sel.value = defaultP2[idx] || rosterNames[1];
      sel.addEventListener('change', () => onPokeChange('p2', idx, sel.value));
    });

    // Render customization drawers
    renderCustomDrawer('p1');
    renderCustomDrawer('p2');
  }

  function createDefaultPokeConfig(name) {
    const base = pokemonDb[name] || {};
    return {
      name,
      ability: base.defaultAbility || (base.abilities ? base.abilities[0] : 'Static'),
      item: base.defaultItem || 'Leftovers',
      nature: base.defaultNature || 'Adamant',
      evs: base.defaultEvs || evPresetsList[0] || 'Physical Sweeper (252 Atk / 252 Spe / 4 SpD)',
      moves: base.defaultMoves ? [...base.defaultMoves] : ['Tackle', 'Protect', 'Rest', 'Body Slam']
    };
  }

  function onPokeChange(player, slotIdx, newName) {
    const team = player === 'p1' ? teamP1 : teamP2;
    team[slotIdx] = createDefaultPokeConfig(newName);
    renderCustomDrawer(player);
  }

  function renderCustomDrawer(player) {
    const container = player === 'p1' ? p1SlotsContainer : p2SlotsContainer;
    const team = player === 'p1' ? teamP1 : teamP2;

    container.innerHTML = team.map((poke, slotIdx) => {
      const base = pokemonDb[poke.name] || {};
      const legalAbilities = base.abilities || [poke.ability];
      const legalMoves = base.legalMoves || poke.moves;

      const abilityOpts = legalAbilities.map(a => `<option value="${a}" ${a === poke.ability ? 'selected' : ''}>${a}</option>`).join('');
      const itemOpts = itemsList.map(it => `<option value="${it}" ${it === poke.item ? 'selected' : ''}>${it}</option>`).join('');
      const natureOpts = naturesList.map(n => `<option value="${n}" ${n === poke.nature ? 'selected' : ''}>${n}</option>`).join('');
      const evOpts = evPresetsList.map(ev => `<option value="${ev}" ${ev === poke.evs ? 'selected' : ''}>${ev}</option>`).join('');

      const renderMoveSelect = (moveIdx) => {
        const curMove = poke.moves[moveIdx] || legalMoves[moveIdx] || legalMoves[0];
        const moveOpts = legalMoves.map(m => `<option value="${m}" ${m === curMove ? 'selected' : ''}>${m}</option>`).join('');
        return `
          <div class="field-group">
            <label>Move ${moveIdx + 1}</label>
            <select class="custom-select move-select" data-player="${player}" data-slot="${slotIdx}" data-move="${moveIdx}">
              ${moveOpts}
            </select>
          </div>
        `;
      };

      return `
        <div class="slot-custom-card">
          <div class="slot-card-title">
            <span>Slot ${slotIdx + 1}: ${poke.name} (${base.types ? base.types.join('/') : ''})</span>
            <span style="font-size:9px;color:#94a3b8;">BST ${base.bst || 500}</span>
          </div>

          <div class="custom-grid-2">
            <div class="field-group">
              <label>Ability</label>
              <select class="custom-select ability-select" data-player="${player}" data-slot="${slotIdx}">
                ${abilityOpts}
              </select>
            </div>
            <div class="field-group">
              <label>Held Item</label>
              <select class="custom-select item-select" data-player="${player}" data-slot="${slotIdx}">
                ${itemOpts}
              </select>
            </div>
          </div>

          <div class="custom-grid-2">
            <div class="field-group">
              <label>Nature</label>
              <select class="custom-select nature-select" data-player="${player}" data-slot="${slotIdx}">
                ${natureOpts}
              </select>
            </div>
            <div class="field-group">
              <label>EV Spread</label>
              <select class="custom-select ev-select" data-player="${player}" data-slot="${slotIdx}">
                ${evOpts}
              </select>
            </div>
          </div>

          <div class="custom-grid-4">
            ${renderMoveSelect(0)}
            ${renderMoveSelect(1)}
            ${renderMoveSelect(2)}
            ${renderMoveSelect(3)}
          </div>
        </div>
      `;
    }).join('');

    // Attach change listeners inside this drawer
    container.querySelectorAll('.ability-select').forEach(sel => {
      sel.addEventListener('change', (e) => {
        const slot = parseInt(e.target.dataset.slot, 10);
        team[slot].ability = e.target.value;
      });
    });

    container.querySelectorAll('.item-select').forEach(sel => {
      sel.addEventListener('change', (e) => {
        const slot = parseInt(e.target.dataset.slot, 10);
        team[slot].item = e.target.value;
      });
    });

    container.querySelectorAll('.nature-select').forEach(sel => {
      sel.addEventListener('change', (e) => {
        const slot = parseInt(e.target.dataset.slot, 10);
        team[slot].nature = e.target.value;
      });
    });

    container.querySelectorAll('.ev-select').forEach(sel => {
      sel.addEventListener('change', (e) => {
        const slot = parseInt(e.target.dataset.slot, 10);
        team[slot].evs = e.target.value;
      });
    });

    container.querySelectorAll('.move-select').forEach(sel => {
      sel.addEventListener('change', (e) => {
        const slot = parseInt(e.target.dataset.slot, 10);
        const moveIdx = parseInt(e.target.dataset.move, 10);
        team[slot].moves[moveIdx] = e.target.value;
      });
    });
  }

  const btnShowWinner = document.getElementById('btnShowWinner');
  let pendingWinnerInfo = '';
  let pendingErrorDetails = '';

  function setErrorDetails(errors) {
    pendingErrorDetails = Array.isArray(errors) ? errors.join('\n\n') : String(errors || 'Unknown algorithm error.');
    btnShowError.disabled = false;
  }

  function closeErrorModal() {
    errorModal.classList.add('hidden');
  }

  btnShowError.addEventListener('click', () => {
    errorDetails.textContent = pendingErrorDetails;
    errorModal.classList.remove('hidden');
  });
  btnCloseError.addEventListener('click', closeErrorModal);
  errorModal.addEventListener('click', (event) => {
    if (event.target === errorModal) closeErrorModal();
  });

  if (btnShowWinner) {
    btnShowWinner.addEventListener('click', () => {
      if (winnerOutput.classList.contains('hidden')) {
        winnerOutput.textContent = pendingWinnerInfo ? `Winner: ${pendingWinnerInfo}` : 'No battle completed yet.';
        winnerOutput.classList.remove('hidden');
        btnShowWinner.textContent = 'Hide Winner';
      } else {
        winnerOutput.classList.add('hidden');
        btnShowWinner.textContent = '🏆 Show Winner';
      }
    });
  }

  // Simulation Start
  btnStart.addEventListener('click', async () => {
    btnStart.disabled = true;
    btnStart.textContent = 'Simulating...';
    
    // Reset winner button
    if (btnShowWinner) {
      btnShowWinner.disabled = true;
      btnShowWinner.classList.remove('ready');
      btnShowWinner.textContent = 'Show Winner';
    }
    winnerOutput.classList.add('hidden');
    winnerOutput.textContent = '';
    pendingErrorDetails = '';
    btnShowError.disabled = true;
    closeErrorModal();

    const formData = new FormData();
    formData.append('p1Name', 'Player 1');
    formData.append('p1_custom_team', JSON.stringify(teamP1));

    if (p1FileInput.files && p1FileInput.files[0]) {
      formData.append('p1_file', p1FileInput.files[0]);
    } else {
      formData.append('p1Sample', p1SampleSelect.value);
    }

    formData.append('p2Name', 'Player 2');
    formData.append('p2_custom_team', JSON.stringify(teamP2));

    if (p2FileInput.files && p2FileInput.files[0]) {
      formData.append('p2_file', p2FileInput.files[0]);
    } else {
      formData.append('p2Sample', p2SampleSelect.value);
    }

    try {
      const response = await fetch('/api/simulate-ml', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        const errors = result.validationErrors || [result.error || 'Battle failed'];
        setErrorDetails(errors);
        throw new Error(result.error || 'Battle failed');
      }

      // Update simulation replay on the left
      if (result.replayHtml) {
        showdownFrame.srcdoc = result.replayHtml;
        showdownFrame.removeAttribute('src');
      } else {
        showdownFrame.src = `/replay/${result.battleId}`;
      }

      // Set winner info for the Show Winner button
      pendingWinnerInfo = `${result.winner} (Finished in ${result.turns} turns)`;
      if (btnShowWinner) {
        btnShowWinner.disabled = false;
        btnShowWinner.classList.add('ready');
        btnShowWinner.textContent = 'Show Winner';
      }

    } catch (err) {
      console.error(err);
      if (!pendingErrorDetails) setErrorDetails(err.message || 'Battle failed');
      winnerOutput.classList.remove('hidden');
      winnerOutput.textContent = 'Testing failed. Click Show Error for details.';
    } finally {
      btnStart.disabled = false;
      btnStart.textContent = 'Start Simulation';
    }
  });
});
