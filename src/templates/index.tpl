{% extends "base.tpl" %}
{% block title %}Home{% endblock %}
{% block content %}
  <p>
  <a href="/upload/tabular-form">Upload tabular data</a>
  </p>

  <h1>Tags</h1>
  <ul>
    {% for tag in tags %}
      <li>{{ tag.name }} : {{ tag.count }}</li>
    {% endfor %}
  </ul>

  <h1>Datasets</h1>
  
  <table class="table table-bordered table-striped">
    <thead>
      <tr>
          <th>Name</th>
          <th>Description</th>
      </tr>
    </thead>
    
    <tbody>
      {% for ds in datasets %}
      <tr>
        <td><a href="/dataset/show/{{ds.dataset_id}}">{{ ds.name }}</a></td>
        <td>{{ ds.description }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

{% endblock %}