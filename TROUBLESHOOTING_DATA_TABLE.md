# Troubleshooting: Data Table Not Showing

## Issue
The interactive data table with pagination and filters is not appearing after file upload.

## Code Status
✅ **No code was erased** - All code is present:
- `InteractiveDataTable.tsx` exists and has full implementation
- `FileUpload.tsx` imports and renders `InteractiveDataTable`
- Backend `data.py` router exists with endpoints
- API functions `getTableData` and `getTableColumns` exist

## Possible Causes

### 1. **uploadedFileId State Not Set**
**Symptom**: Table doesn't appear after upload
**Check**: 
- Open browser console (F12)
- Look for: `"File uploaded successfully, setting uploadedFileId: ..."`
- Check if `uploadedFileId` is being set in state

**Solution**: 
- Verify file upload completes successfully
- Check that `response.file_id` is returned from API
- Verify state is updated: `setUploadedFileId(lastFileId)`

### 2. **Backend Endpoints Not Accessible**
**Symptom**: Table shows loading spinner or error message
**Check**:
- Open browser console (F12) → Network tab
- Look for requests to `/api/data/table/{table_name}`
- Check if requests are failing (404, 500, etc.)
- Verify backend server is running on port 8000

**Solution**:
- Start backend server: `uvicorn app.main:app --reload`
- Verify endpoint exists: `GET /api/data/table/{table_name}`
- Check backend logs for errors

### 3. **Table Name Mismatch**
**Symptom**: "Table not found" error
**Check**:
- Verify table name matches `file_id` exactly
- Check database for table existence
- Verify table was created during upload

**Solution**:
- Check upload logs for table creation
- Verify SQL table exists in database
- Check table name format (should match file_id)

### 4. **localStorage Not Restoring**
**Symptom**: Table doesn't show after page refresh
**Check**:
- Open browser console (F12) → Application tab → Local Storage
- Look for: `lastUploadedFile_{userId}`
- Check if value exists and matches a file_id

**Solution**:
- Clear localStorage and re-upload file
- Check console for restoration logs
- Verify file still exists in catalogs

### 5. **Component Not Rendering**
**Symptom**: No table, no error, nothing in console
**Check**:
- Verify `uploadedFileId` is not null
- Check if `InteractiveDataTable` component is in DOM
- Verify component is not hidden by CSS

**Solution**:
- Add console.log to verify rendering
- Check React DevTools for component tree
- Verify conditional rendering logic

## Debugging Steps

### Step 1: Check Browser Console
1. Open browser console (F12)
2. Look for error messages
3. Check for network errors
4. Look for console.log messages about file upload

### Step 2: Check Network Requests
1. Open browser console (F12) → Network tab
2. Upload a file
3. Look for:
   - `POST /api/upload/` - Should return `file_id`
   - `GET /api/data/table/{file_id}/columns` - Should return columns
   - `GET /api/data/table/{file_id}?page=1&page_size=10` - Should return data

### Step 3: Check localStorage
1. Open browser console (F12) → Application tab → Local Storage
2. Look for: `lastUploadedFile_{userId}`
3. Verify value matches a file_id from your uploads
4. Check if value exists after page refresh

### Step 4: Check Backend Logs
1. Check backend terminal/console
2. Look for errors during:
   - File upload
   - Table creation
   - Data retrieval
3. Verify endpoints are being called

### Step 5: Verify Table Exists in Database
1. Open SQLite database: `rag.db`
2. Check if table exists: `SELECT name FROM sqlite_master WHERE type='table';`
3. Verify table name matches `file_id`
4. Check if table has data: `SELECT COUNT(*) FROM "{file_id}";`

## Quick Fixes

### Fix 1: Clear localStorage and Re-upload
```javascript
// In browser console:
localStorage.clear();
// Then refresh page and re-upload file
```

### Fix 2: Verify Backend is Running
```bash
# Check if backend is running
curl http://localhost:8000/health

# Should return: {"status":"healthy"}
```

### Fix 3: Check Backend Endpoints
```bash
# Test data endpoint
curl http://localhost:8000/api/data/table/{your_file_id}/columns

# Should return column names
```

### Fix 4: Restart Backend
```bash
# Stop backend (Ctrl+C)
# Restart backend
cd backend
uvicorn app.main:app --reload
```

## Expected Behavior

### After File Upload:
1. ✅ File uploads successfully
2. ✅ `uploadedFileId` state is set
3. ✅ `InteractiveDataTable` component renders
4. ✅ Table shows "Loading data table..." message
5. ✅ Table fetches columns from `/api/data/table/{file_id}/columns`
6. ✅ Table fetches data from `/api/data/table/{file_id}?page=1&page_size=10`
7. ✅ Table displays data with pagination, search, and sorting

### After Page Refresh:
1. ✅ `useEffect` runs on mount
2. ✅ Checks localStorage for `lastUploadedFile_{userId}`
3. ✅ Verifies file exists in catalogs
4. ✅ Sets `uploadedFileId` state
5. ✅ Table renders automatically

## Common Issues and Solutions

### Issue: Table shows "Error loading data table"
**Cause**: Backend endpoint not accessible or table doesn't exist
**Solution**: 
- Check backend is running
- Verify table exists in database
- Check backend logs for errors

### Issue: Table shows "Loading..." forever
**Cause**: API request hanging or failing silently
**Solution**:
- Check network tab for pending requests
- Verify backend endpoint is responding
- Check for CORS errors

### Issue: Table doesn't appear after upload
**Cause**: `uploadedFileId` not set or component not rendering
**Solution**:
- Check console for upload success message
- Verify `setUploadedFileId` is called
- Check React DevTools for component state

### Issue: Table disappears after refresh
**Cause**: localStorage not restoring or file deleted
**Solution**:
- Check localStorage for file_id
- Verify file still exists in catalogs
- Check console for restoration logs

## Verification Checklist

- [ ] Backend server is running on port 8000
- [ ] Frontend is running on port 3000
- [ ] File upload completes successfully
- [ ] `file_id` is returned from upload API
- [ ] `uploadedFileId` state is set after upload
- [ ] `InteractiveDataTable` component renders
- [ ] Backend endpoints `/api/data/table/{file_id}` are accessible
- [ ] Table exists in database with correct name
- [ ] localStorage contains `lastUploadedFile_{userId}`
- [ ] No errors in browser console
- [ ] No errors in backend logs

## Next Steps

1. **Check Browser Console**: Look for errors or logs
2. **Check Network Tab**: Verify API requests are being made
3. **Check Backend Logs**: Look for errors or missing endpoints
4. **Verify Database**: Check if table exists and has data
5. **Test Manually**: Try uploading a new file and see if table appears

## Contact Points

If issue persists:
1. Check browser console for specific error messages
2. Check backend logs for API errors
3. Verify all endpoints are registered in `main.py`
4. Test endpoints manually using curl or Postman

---

## Code Locations

- **Frontend Table Component**: `frontend/src/components/DataTable/InteractiveDataTable.tsx`
- **Frontend Upload Component**: `frontend/src/components/Upload/FileUpload.tsx`
- **Backend Data Router**: `backend/app/routers/data.py`
- **Backend Main App**: `backend/app/main.py`
- **API Client**: `frontend/src/services/api.ts`

