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


// Render the notes list
function renderNotesList() {
    const notesList = document.getElementById('notes-list');
    notesList.innerHTML = ''; // Clear the list
    
    if (notes.length === 0) {
        const emptyMessage = document.createElement('div');
        emptyMessage.className = 'empty-notes-message';
        emptyMessage.textContent = 'No notes yet. Click "New" to create your first note!';
        notesList.appendChild(emptyMessage);
        return;
    }
    
    // Sort notes by updated date (newest first)
    const sortedNotes = [...notes].sort((a, b) => {
        return new Date(b.updatedAt) - new Date(a.updatedAt);
    });
    
    sortedNotes.forEach(note => {
        const noteItem = document.createElement('div');
        noteItem.className = 'note-item';
        if (note._id === currentNoteId) {
            noteItem.classList.add('active');
        }
        noteItem.dataset.id = note._id;
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
    });
}

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
        content: 'Let your imagination run wild!',
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
    // if (!currentNoteId) return;
    
    var title = document.getElementById('note-title-input').value;
    var content = document.getElementById('note-content').value;
    
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
            // Update local notes array
            if (currentNoteId === 'new') {
                // For a new note, update the ID and replace in the notes array
                currentNoteId = data.note_id;
                const index = notes.findIndex(note => note._id === 'new');
                if (index !== -1) {
                    notes[index] = data.note;
                }
            } else {
                // For existing notes, update the note in the array
                const index = notes.findIndex(note => note._id === currentNoteId);
                if (index !== -1) {
                    notes[index] = data.note;
                }
            }
            
            // Refresh UI
            renderNotesList();
            
            // Show feedback
            const saveBtn = document.getElementById('save-note-btn');
            const originalHTML = saveBtn.innerHTML;
            saveBtn.innerHTML = '<i class="fas fa-check"></i> Saved';
            
            setTimeout(() => {
                saveBtn.innerHTML = originalHTML;
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