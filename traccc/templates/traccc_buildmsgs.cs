<h3>Build Messages</h3>
<ul>
  <li>Time to build: <?cs var:cc.timetobuild ?>
</ul>
<table class="code">
 <thead><tr>
   <th class="lineno">Type</th><th class="content">Messages</th>
 </tr></thead>
 <tbody><?cs
 each:item = cc.messages ?><tr class="<?cs var:item.type?>">
 <th class="lineno"><?cs var:item.type ?></th>
 <td><?cs var:item.msg ?></td></tr>
 <?cs /each ?>
 </tbody>
</table>