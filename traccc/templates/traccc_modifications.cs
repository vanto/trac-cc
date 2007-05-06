<?cs if:len(modifications) != 0 ?>
<h3>Modifications since the last build</h3>
<table class="listing modification">
 <thead><tr>
   <th>File</th><th>Chgset</th><th>Action</th><th>Date</th><th>User</th><th>Comment</th>
 </tr></thead>
 <tbody><?cs
 each:item = modifications ?><tr>
 <th><?cs if:item.filename_href ?><a href="<?cs var:item.filename_href
 ?>"><?cs var:item.filename ?></a><?cs else ?><?cs var:item.filename
 ?><?cs /if ?></td><td><?cs if:item.revision ?><?cs if:item.revision_href ?><a href="<?cs var:item.revision_href ?>">[<?cs
 var:item.revision ?>]</a><?cs else ?>[<?cs
 var:item.revision ?>]<?cs /if ?><?cs /if ?></th>
 <td><?cs var:item.action ?></td>
 <td><?cs var:item.date ?></td>
 <td><?cs var:item.user ?></td>
 <td><?cs var:item.comment ?></td></tr>
 <?cs /each ?>
 </tbody>
</table>
<?cs /if ?>