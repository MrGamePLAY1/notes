// Global variables
let currentNoteId = null;
let notes = [];

// Load notes when the page loads
document.addEventListener('DOMContentLoaded', () => {
    loadNotes();
});

// Function to load notes from the server
function loadNotes() {
    // For now, we'll use sample data
    // In a real app, you would fetch from your backend API
    notes = [
        { id: 1, title: 'Sample Note 1', content: 'This is a sample note.', updatedAt: new Date() },
        { id: 2, title: 'Ideas for Project', content: 'List of ideas for my new project...', updatedAt: new Date() }
    ];
    
    renderNotesList();
    
    // If there are notes, select the first one
    if (notes.length > 0) {
        selectNote(notes[0].id);
    }
}

// Render the notes list in the sidebar
function renderNotesList() {
    const notesList = document.getElementById('notes-list');
    notesList.innerHTML = '';
    
    notes.forEach(note => {
        const noteItem = document.createElement('div');
        noteItem.className = 'note-item';
        noteItem.dataset.id = note.id;
        noteItem.onclick = () => selectNote(note.id);
        
        const noteTitle = document.createElement('div');
        noteTitle.className = 'note-item-title';
        noteTitle.textContent = note.title || 'Untitled';
        
        const noteDate = document.createElement('div');
        noteDate.className = 'note-item-date';
        noteDate.textContent = formatDate(note.updatedAt);
        
        noteItem.appendChild(noteTitle);
        noteItem.appendChild(noteDate);
        notesList.appendChild(noteItem);
        
        // Mark the current note as selected
        if (note.id === currentNoteId) {
            noteItem.classList.add('selected');
        }
    });
}

// Select a note to edit
function selectNote(id) {
    currentNoteId = id;
    const note = notes.find(note => note.id === id);
    
    if (note) {
        document.getElementById('note-title-input').value = note.title || '';
        document.getElementById('note-content').value = note.content || '';
        
        // Update selected state in the list
        document.querySelectorAll('.note-item').forEach(item => {
            item.classList.toggle('selected', parseInt(item.dataset.id) === id);
        });
    }
}

// Create a new note
function createNewNote() {
    const newId = notes.length > 0 ? Math.max(...notes.map(note => note.id)) + 1 : 1;
    const newNote = {
        id: newId,
        title: 'Untitled Note',
        content: '',
        updatedAt: new Date()
    };
    
    notes.unshift(newNote); // Add to beginning of array
    renderNotesList();
    selectNote(newId);
    
    // Focus on the title input
    document.getElementById('note-title-input').focus();
}

// Save the current note
function saveCurrentNote() {
    if (currentNoteId === null) return;
    
    const title = document.getElementById('note-title-input').value;
    const content = document.getElementById('note-content').value;
    
    const noteIndex = notes.findIndex(note => note.id === currentNoteId);
    if (noteIndex !== -1) {
        notes[noteIndex].title = title;
        notes[noteIndex].content = content;
        notes[noteIndex].updatedAt = new Date();
        
        renderNotesList();
        
        // Show a save confirmation
        const saveBtn = document.querySelector('.save-btn');
        saveBtn.textContent = 'Saved!';
        setTimeout(() => {
            saveBtn.textContent = 'Save';
        }, 1500);
    }
}

// Delete the current note
function deleteCurrentNote() {
    if (currentNoteId === null) return;
    
    if (confirm('Are you sure you want to delete this note?')) {
        notes = notes.filter(note => note.id !== currentNoteId);
        
        renderNotesList();
        
        // Clear the editor if there are no notes left
        if (notes.length === 0) {
            document.getElementById('note-title-input').value = '';
            document.getElementById('note-content').value = '';
            currentNoteId = null;
        } else {
            // Select the first note
            selectNote(notes[0].id);
        }
    }
}

// Format date for display
function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric'
    });
}