<?cs include "header.cs"?>
<div id="ctxtnav" class="nav">
 <h2>About Navigation</h2>
 <ul>
  <li class="first last"><a href="<?cs
    var:cc.baseLink ?>">Overview</a></li>
 </ul>
</div>
<div id="content" class="cc<?cs if:cc.page ?>_<?cs var:cc.page ?><?cs /if ?>">
<h1>CruiseControl Status Page</h1>
<p><?cs var:cc.buildstatus ?></p>
<h2>Builds</h2>
<p>
<?cs each:build = cc.builds ?>
   <?cs if:build.successful ?><img src="<?cs var:chrome.href ?>/traccc/ccsuccess.gif" border="0"/> 
   <?cs else ?><img src="<?cs var:chrome.href ?>/traccc/ccerror.gif" border="0"/>
   <?cs /if ?>
   <a href="<?cs var:cc.baseLink ?>/<?cs var:build.id ?>"><?cs var:build.datetimeStr ?> <?cs var:build.label ?></a><br/>
<?cs /each ?>
</p>
</div>
<?cs include "footer.cs"?>
