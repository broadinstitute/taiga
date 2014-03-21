{% extends "base.tpl" %}
{% block title %}Home{% endblock %}
{% block content %}
  <h1>Find</h1>
    <ul>
    {% for dataset in datasets %}
      <li><a href="/dataset/show/{{ dataset.id }}">{{ dataset.id }}</a></li>
    {% endfor %}
    </ul>
  <h1>Upload CSV</h1>

  <form class="form-horizontal" role="form" method="post" action="/upload" enctype="multipart/form-data">
    <div class="form-group">
      <label for="inputName" class="col-sm-2 control-label">Dataset Name</label>
      <div class="col-sm-10">
        <input type="text" class="form-control" id="inputName" placeholder="Name" name="name">
      </div>
    </div>
    <div class="form-group">
      <label for="inputOwner" class="col-sm-2 control-label">Owner</label>
      <div class="col-sm-10">
        <input type="text" class="form-control" id="inputOwner" placeholder="Owner" name="owner">
      </div>
    </div>
    <div class="form-group">
      <label for="inputColumnValues" class="col-sm-2 control-label">Columns represent</label>
      <div class="col-sm-10">
        <input type="text" class="form-control" id="inputColumnValues" placeholder="Description" name="columns">
      </div>
    </div>
    <div class="form-group">
      <label for="inputRowValues" class="col-sm-2 control-label">Rows represent</label>
      <div class="col-sm-10">
        <input type="text" class="form-control" id="inputRowValues" placeholder="Description" name="rows">
      </div>
    </div>
    <div class="form-group">
      <label for="inputDescription" class="col-sm-2 control-label">Description</label>
      <div class="col-sm-10">
        <textarea id="inputDescription" class="form-control" rows="3" name="description"></textarea>
      </div>
    </div>
    <div class="form-group">
      <label for="inputFile" class="col-sm-2 control-label">File</label>
      <div class="col-sm-10">
        <input type="file" class="form-control" id="inputFile" name="file">
      </div>
    </div>
    <div class="form-group">
      <div class="col-sm-offset-2 col-sm-10">
        <button type="submit" class="btn btn-default">Submit</button>
      </div>
    </div>
  </form>
  
  <h1>Slice</h1>
{% endblock %}