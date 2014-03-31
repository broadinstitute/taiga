{% extends "base.tpl" %}
{% block title %}Upload Tabular File{% endblock %}
{% block content %}

  <h1>Upload CSV as a new
    {% if new_version %} 
      Version of an existing Dataset
    {% else %}
      Dataset
    {% endif %}
  </h1>

  <form class="form-horizontal" role="form" method="post" action="/upload/tabular" enctype="multipart/form-data">
    {% if new_version %} 
      <input type="hidden" name="overwrite_existing" value="true">
    {% endif %}
    <div class="form-group">
      <label for="inputName" class="col-sm-2 control-label">Dataset Name</label>
      <div class="col-sm-10">
        <input type="text" {% if new_version %} disabled value="{{name}}" {% endif %} class="form-control" id="inputName" placeholder="Name" name="name">
      </div>
    </div>
    <div class="form-group">
      <label for="inputColumnValues" class="col-sm-2 control-label">Columns represent</label>
      <div class="col-sm-10">
        <input type="text" class="form-control" id="inputColumnValues" placeholder="Description" name="columns" value="{{columns}}">
      </div>
    </div>
    <div class="form-group">
      <label for="inputRowValues" class="col-sm-2 control-label">Rows represent</label>
      <div class="col-sm-10">
        <input type="text" class="form-control" id="inputRowValues" placeholder="Description" name="rows" value="{{rows}}">
      </div>
    </div>
    <div class="form-group">
      <label for="inputDescription" class="col-sm-2 control-label">Description</label>
      <div class="col-sm-10">
        <textarea id="inputDescription" class="form-control" rows="3" name="description">{{description}}</textarea>
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

{% endblock %}
