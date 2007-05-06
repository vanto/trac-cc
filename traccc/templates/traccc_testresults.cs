<h3>Test Results for <?cs var:cc.testsuite?></h3>
<table class="listing testresults">
 <thead><tr>
   <th>Status</th><th>Test</th><th>Time</th>
 </tr></thead>
 <tbody><?cs each:item = cc.testresults ?><tr>
 <th class="<?cs if:item.failed ?>failed<?cs else ?>success<?cs /if ?>">&nbsp;</th>
 <td><?cs var:item.name ?></td>
 <td><?cs var:item.time ?></td></tr>
 <?cs if:item.failed ?><tr><td></td><td colspan="2"><pre><?cs
 var:item.msg ?></pre></tr><?cs /if ?>

 <?cs /each ?>
 </tbody>
</table>
