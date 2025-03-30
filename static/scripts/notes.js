// Global variables
let currentNoteId = null;
let notes = [];

// Load notes when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Set up event listeners
    document.getElementById('new-note-btn').addEventListener('click', createNewNote);
    document.getElementById('save-note-btn').addEventListener('click', saveCurrentNote);
    document.getElementById('delete-note-btn').addEventListener('click', showDeleteModal);
    document.getElementById('cancel-delete-btn').addEventListener('click', hideDeleteModal);
    document.getElementById('confirm-delete-btn').addEventListener('click', deleteCurrentNote);
    
    // Load notes
    fetchNotesFromServer();
});

// Function to fetch notes from the server
function fetchNotesFromServer() {
    fetch('/api/notes')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch notes');
            }
            return response.json();
        })
        .then(data => {
            notes = data.notes;
            renderNotesList();
            
            // If there are notes, select the first one
            if (notes.length > 0) {
                selectNote(notes[0]._id);
            } else {
                // If no notes, show empty state
                clearEditor();
            }
        })
        .catch(error => {
            console.error('Error fetching notes:', error);
        });
}

// Clear the editor
function clearEditor() {
    document.getElementById('note-title-input').value = '';
    document.getElementById('note-content').value = '';
    currentNoteId = null;
}

// Render the notes list in the sidebar
function renderNotesList() {
    const notesList = document.getElementById('notes-list');
    notesList.innerHTML = '';
    
    if (notes.length === 0) {
        const emptyMessage = document.createElement('div');
        emptyMessage.className = 'empty-notes-message';
        emptyMessage.textContent = 'No notes yet. Click "New" to create your first note!';
        notesList.appendChild(emptyMessage);
        return;
    }
    
    notes.forEach(note => {
        const noteItem = document.createElement('div');
        noteItem.className = 'note-item';
        noteItem.dataset.id = note._id; // Use _id from MongoDB
        noteItem.onclick = () => selectNote(note._id);
        
        const noteContent = document.createElement('div');
        noteContent.className = 'note-item-content';
        
        const noteTitle = document.createElement('h3');
        noteTitle.className = 'note-item-title';
        noteTitle.textContent = note.title || 'Untitled';
        
        const notePreview = document.createElement('p');
        notePreview.className = 'note-item-preview';
        notePreview.textContent = note.content ? (note.content.length > 60 ? 
            note.content.substring(0, 60) + '...' : note.content) : '';
        
        const noteMeta = document.createElement('div');
        noteMeta.className = 'note-item-meta';
        
        const noteDate = document.createElement('span');
        noteDate.className = 'note-date';
        noteDate.textContent = formatDate(note.updatedAt);
        
        noteMeta.appendChild(noteDate);
        noteContent.appendChild(noteTitle);
        noteContent.appendChild(notePreview);
        noteContent.appendChild(noteMeta);
        noteItem.appendChild(noteContent);
        notesList.appendChild(noteItem);
        
        // Mark the current note as selected
        if (note._id === currentNoteId) {
            noteItem.classList.add('active');
        }
    });
}

// Select a note to edit
function selectNote(id) {
    currentNoteId = id;
    const note = notes.find(note => note._id === id);
    
    if (note) {
        document.getElementById('note-title-input').value = note.title || '';
        document.getElementById('note-content').value = note.content || '';
        
        // Update selected state in the list
        document.querySelectorAll('.note-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.id === id) {
                item.classList.add('active');
            }
        });
    }
}

// Show delete confirmation modal
function showDeleteModal() {
    if (!currentNoteId) return;
    document.getElementById('delete-modal').style.display = 'flex';
}

// Hide delete confirmation modal
function hideDeleteModal() {
    document.getElementById('delete-modal').style.display = 'none';
}

// Create a new note
function createNewNote() {
    const newNote = {
        _id: 'new', // This will be replaced with the MongoDB ID after saving
        title: 'Untitled Note',
        content: '',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
    };
    
    // Create temporary UI representation
    notes.unshift(newNote);
    renderNotesList();
    selectNote('new');
    
    // Focus on the title input
    document.getElementById('note-title-input').focus();
}

// Save the current note
function saveCurrentNote() {
    if (!currentNoteId) return;
    
    const title = document.getElementById('note-title-input').value;
    const content = document.getElementById('note-content').value;
    
    // Basic validation
    if (!title.trim()) {
        alert('Please enter a title for your note');
        document.getElementById('note-title-input').focus();
        return;
    }
    
    // Prepare note data
    const noteData = {
        _id: currentNoteId,
        title: title,
        content: content
    };
    
    // Send to server
    fetch('/save-note', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(noteData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // If this was a new note, update its ID
            if (currentNoteId === 'new') {
                const index = notes.findIndex(note => note._id === 'new');
                if (index !== -1) {
                    notes[index]._id = data.note_id;
                    currentNoteId = data.note_id;
                }
            }
            
            // Update the note in our array
            const noteIndex = notes.findIndex(note => note._id === currentNoteId);
            if (noteIndex !== -1) {
                notes[noteIndex].title = title;
                notes[noteIndex].content = content;
                notes[noteIndex].updatedAt = new Date().toISOString();
            }
            
            // Refresh the UI
            renderNotesList();
            
            // Show save confirmation
            const saveBtn = document.getElementById('save-note-btn');
            const originalText = saveBtn.innerHTML;
            saveBtn.innerHTML = '<i class="fas fa-check"></i> Saved';
            
            setTimeout(() => {
                saveBtn.innerHTML = originalText;
            }, 1500);
        } else {
            alert('Error saving note: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error saving note:', error);
        alert('Failed to save note. Please try again.');
    });
}

// Delete the current note
function deleteCurrentNote() {
    if (!currentNoteId || currentNoteId === 'new') {
        hideDeleteModal();
        return;
    }
    
    fetch('/delete-note', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ note_id: currentNoteId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove from our array
            notes = notes.filter(note => note._id !== currentNoteId);
            
            // Hide modal
            hideDeleteModal();
            
            // Refresh UI
            renderNotesList();
            
            // Select another note or clear editor
            if (notes.length > 0) {
                selectNote(notes[0]._id);
            } else {
                clearEditor();
            }
        } else {
            alert('Error deleting note: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error deleting note:', error);
        alert('Failed to delete note. Please try again.');
    });
}

// Format date for display
function formatDate(date) {
    const dateObj = new Date(date);
    return dateObj.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric'
    });
}