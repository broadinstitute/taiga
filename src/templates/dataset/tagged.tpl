{% extends "base.tpl" %}

{% block title %}Datasets with tag {{ tag }} {% endblock %}
{% block content %}
  <a href="/">Home</a>
  <h1>
    Datasets tagged {{ tag }}
  </h1>

  <ul>
    {% for dataset in datasets %}
    <li>
      <a href="/dataset/show/{{ dataset.id }}">{{ dataset.name }}</a>
    </li>
    {% endfor %}
  </ul>

{% endblock %}
