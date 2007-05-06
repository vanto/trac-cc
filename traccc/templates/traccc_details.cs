<?cs include "header.cs"?>
<div id="ctxtnav" class="nav">
 <h2>About Navigation</h2>
 <ul>
  <li class="first last"><a href="<?cs
    var:cc.baseLink ?>">Overview</a></li>
 </ul>
</div>
<div id="content" class="traccc">
<h1>CruiseControl Details Page</h1>
<p>
   <?cs if:cc.build.successful ?><img src="<?cs var:chrome.href ?>/traccc/ccsuccess.gif" border="0"/> 
   <?cs else ?><img src="<?cs var:chrome.href ?>/traccc/ccerror.gif" border="0"/>
   <?cs /if ?>
   <b>Build from <?cs var:cc.build.datetimeStr ?> <?cs var:cc.build.label ?></b>
</p>
<?cs var:cc.html_result ?>
</div>
<?cs include "footer.cs"?>
