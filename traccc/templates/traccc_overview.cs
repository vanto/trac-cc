<?cs include "header.cs"?>
<div id="ctxtnav" class="nav">
 <h2>About Navigation</h2>
 <ul>
  <li class="first last"><a href="<?cs
    var:cc.baseLink ?>">Overview</a></li>
 </ul>
</div>
<div id="content" class="traccc">
<h1>CruiseControl Status Page</h1>
<h2>Projects</h2>
<?cs each:project = cc.data[1]?>
<h3 style="margin: 0px; margin-top: 15px;"><img src="<?cs var:chrome.href?>/traccc/<?cs if:project.status
?>ccsuccess.gif<?cs else ?>ccerror.gif<?cs /if ?>" border="0"/> <?cs var:project.name?></h3>
<?cs var:project.info?><?cs if:!project.status ?><br/>
Last successful build: <?cs var:project.lastsuccess?>
<?cs /if ?>
<?cs /each ?>

<h2>Builds</h2>
<table class="listing ccbuilds">
 <thead><tr>
   <th>Status</th><th>Build Id</th><th>Build Label</th><th>Project</th><th>Date</th>
 </tr></thead>
 <tbody>
<?cs each:build = cc.data[0] ?>
 <tr><th class="<?cs if:build.successful ?>success<?cs else ?>failed<?cs /if ?>">&nbsp;</th>
 <td><a href="<?cs var:build.href?>"><?cs var:build.id ?></a></td>
 <td><?cs var:build.label ?></td>
 <td><?cs var:build.project.name ?></td>
 <td><?cs var:build.prettydate ?></td></tr>
<?cs /each ?>
 </tbody>
</table>


</div>
<?cs include "footer.cs"?>
